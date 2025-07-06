"""
Flask Web Application for Bulk Emailer VictorV3

This application provides a web interface for managing email campaigns,
viewing statistics, and user authentication. It uses Flask, SQLAlchemy for
database interactions, and Flask-Login for session management.
It interacts with sender.py for the email sending logic.
"""
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename # For file uploads
import threading # To run sender in background

# Import sender functionalities (assuming sender.py is in the same directory)
try:
    from sender import bulk_send_emails, SMTP_SERVERS, FROM_NAMES, FROM_EMAILS, SUBJECTS, TRACKING_DOMAIN
except ImportError:
    print("CRITICAL: sender.py not found or contains errors. App may not function correctly.")
    # Define placeholders if sender.py is missing, to allow app to start for basic UI dev
    def bulk_send_emails(*args, **kwargs): return {"success": 0, "failed": 0, "details": []}
    SMTP_SERVERS = []
    FROM_NAMES = []
    FROM_EMAILS = []
    SUBJECTS = []
    TRACKING_DOMAIN = "http://localhost:5000"


# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key_!@#$%^&*()_BULK') # Change in production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bulk_emailer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads' # For attachments
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# --- Database Setup ---
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password: str):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies the given password against the stored hash."""
        return check_password_hash(self.password_hash, password)

class Campaign(db.Model):
    """Campaign model to store details of an email campaign."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, default=lambda: f"Campaign_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    subject = db.Column(db.String(255), nullable=False)
    html_body = db.Column(db.Text, nullable=False)
    text_body = db.Column(db.Text, nullable=True)
    recipients = db.Column(db.Text, nullable=False) # Store as JSON list or comma-separated
    attachments_json = db.Column(db.Text, nullable=True) # Store list of attachment paths/info as JSON
    link_url = db.Column(db.String(500), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('campaigns', lazy=True))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Pending") # e.g., Pending, Sending, Sent, Failed

    total_sent = db.Column(db.Integer, default=0)
    total_success = db.Column(db.Integer, default=0)
    total_failed = db.Column(db.Integer, default=0)

class EmailTrack(db.Model):
    """EmailTrack model to log email open events."""
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=True) # Can be null if tracking non-campaign emails
    recipient_email = db.Column(db.String(255), nullable=False, index=True)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    campaign = db.relationship('Campaign', backref=db.backref('opens', lazy='dynamic'))


# --- Login Manager Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Route to redirect to if @login_required is hit by an unauthenticated user.

@login_manager.user_loader
def load_user(user_id: str) -> User:
    """Flask-Login user loader callback."""
    return User.query.get(int(user_id))

# --- Global Variables / State ---
# campaign_sending_status: Dictionary to hold real-time progress of active campaigns.
# Structure: {campaign_id: {"name": str, "total": int, "sent_count": int, "success_count": int, "failed_count": int, "status": str}}
# Note: For production, a more robust solution like Redis or a dedicated task queue (Celery/RQ)
# would be preferable for managing and reporting sending status.
campaign_sending_status = {}


# --- Routes ---

# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handles user logout."""
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new user registration. The first registered user becomes an admin."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'warning')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        # Make the first registered user an admin
        if User.query.count() == 0:
            new_user.is_admin = True
            flash('Admin user registered successfully! Please log in.', 'success')
        else:
            new_user.is_admin = False # Or based on some other logic
            flash('User registered successfully! Please log in.', 'success')

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# --- Main Application Routes ---
@app.route('/')
@login_required
def index():
    """Redirects authenticated users to the dashboard."""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Displays the main dashboard with aggregated stats and charts for the logged-in user."""
    # Basic counts for display
    total_campaigns = Campaign.query.filter_by(user_id=current_user.id).count()

    # Aggregate stats from campaigns for the current user
    user_campaigns = Campaign.query.filter_by(user_id=current_user.id).all()
    total_sent_overall = sum(c.total_sent or 0 for c in user_campaigns)
    total_success_overall = sum(c.total_success or 0 for c in user_campaigns)
    total_failed_overall = sum(c.total_failed or 0 for c in user_campaigns)

    # Total opens for campaigns initiated by the current user
    total_opens_overall = db.session.query(db.func.count(EmailTrack.id))\
                            .join(Campaign)\
                            .filter(Campaign.user_id == current_user.id)\
                            .scalar() or 0

    # Data for Chart.js (Example: Success vs Failed for all user campaigns)
    chart_data = {
        "labels": ["Success", "Failed", "Not Yet Sent/Accounted"],
        "datasets": [{
            "label": "Email Status",
            "data": [
                total_success_overall,
                total_failed_overall,
                total_sent_overall - (total_success_overall + total_failed_overall) # Emails sent but status not yet fully updated or pending
            ],
            "backgroundColor": [
                'rgba(75, 192, 192, 0.7)', # Success - Green
                'rgba(255, 99, 132, 0.7)', # Failed - Red
                'rgba(201, 203, 207, 0.7)'  # Pending/Other - Grey
            ],
            "borderColor": [
                'rgba(75, 192, 192, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(201, 203, 207, 1)'
            ],
            "borderWidth": 1
        }]
    }

    recent_campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(Campaign.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           total_campaigns=total_campaigns,
                           total_sent=total_sent_overall,
                           total_success=total_success_overall,
                           total_failed=total_failed_overall,
                           total_opens=total_opens_overall,
                           chart_data=json.dumps(chart_data),
                           recent_campaigns=recent_campaigns,
                           campaign_sending_status=campaign_sending_status)


@app.route('/campaigns', methods=['GET', 'POST'])
@login_required
def manage_campaigns():
    """
    Handles creation of new campaigns (POST) and listing of existing
    campaigns for the current user (GET).
    """
    if request.method == 'POST': # Create new campaign
        name = request.form.get('name') or f"Campaign_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}" # Auto-generate name if empty
        subject = request.form['subject']
        html_body = request.form['html_body']
        text_body = request.form.get('text_body', '') # Optional
        recipients_str = request.form['recipients'] # Expect comma-separated emails
        link_url = request.form.get('link_url', '')

        # Handle attachments
        uploaded_files_info = []
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    # Store info needed by sender.py; adjust if sender.py expects different dict structure
                    uploaded_files_info.append({'path': filepath, 'filename': filename, 'type': file.mimetype})


        new_campaign = Campaign(
            name=name,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            recipients=recipients_str, # Store as string, parse when sending
            attachments_json=json.dumps(uploaded_files_info) if uploaded_files_info else None,
            link_url=link_url,
            user_id=current_user.id,
            status="Pending"
        )
        db.session.add(new_campaign)
        db.session.commit()
        flash(f'Campaign "{name}" created successfully!', 'success')
        return redirect(url_for('manage_campaigns'))

    campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(Campaign.created_at.desc()).all()
    return render_template('campaigns.html', campaigns=campaigns,
                            smtp_configured=bool(SMTP_SERVERS), # Pass SMTP config status to template
                            from_names=FROM_NAMES, from_emails=FROM_EMAILS, subjects=SUBJECTS)


@app.route('/campaign/<int:campaign_id>/send', methods=['POST'])
@login_required
def send_campaign(campaign_id: int):
    """Initiates the sending process for a specific campaign in a background thread."""
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to send this campaign.', 'danger')
        return redirect(url_for('manage_campaigns'))

    if not SMTP_SERVERS:
        flash('SMTP servers are not configured. Cannot send emails.', 'danger')
        return redirect(url_for('manage_campaigns'))

    if campaign.status == "Sending":
        flash(f'Campaign "{campaign.name}" is already being sent.', 'warning')
        return redirect(url_for('manage_campaigns'))

    recipients_list = [email.strip() for email in campaign.recipients.split(',') if email.strip()]
    if not recipients_list:
        flash('No recipients specified for this campaign.', 'danger')
        campaign.status = "Failed"
        db.session.commit()
        return redirect(url_for('manage_campaigns'))

    attachments = json.loads(campaign.attachments_json) if campaign.attachments_json else []

    # Update campaign status before starting thread
    campaign.status = "Sending"
    campaign.total_sent = len(recipients_list) # Tentative, will be updated by sender
    campaign.total_success = 0
    campaign.total_failed = 0
    db.session.commit()

    # Use global campaign_sending_status for quick UI updates
    campaign_sending_status[campaign.id] = {
        "name": campaign.name,
        "total": len(recipients_list),
        "sent_count": 0,
        "success_count": 0,
        "failed_count": 0,
        "status": "Initializing..."
    }

    # Run bulk_send_emails in a separate thread to avoid blocking the UI
    # Pass necessary database and app context if sender needs to update DB directly
    # For now, sender returns results, and we update DB here or via a status check endpoint
    thread = threading.Thread(target=execute_sending_logic, args=(
        app, # Pass the app instance
        campaign.id,
        recipients_list,
        campaign.subject,
        campaign.html_body,
        campaign.text_body,
        attachments,
        str(campaign.id), # campaign_id for tracking
        campaign.link_url
        # Add num_threads, min_delay, max_delay from config or form
    ))
    thread.daemon = True # Allows main app to exit even if threads are running
    thread.start()

    flash(f'Campaign "{campaign.name}" sending process initiated.', 'info')
    return redirect(url_for('dashboard')) # Or back to campaigns page

def execute_sending_logic(flask_app, db_campaign_id, recipients, subject, html_body, text_body, attachments, tracking_campaign_id, link_url):
    """
    Wrapper function to run email sending logic in a separate thread.
    This function is called by `send_campaign` to offload the blocking
    `bulk_send_emails` call. It requires the Flask app context to perform
    database operations after sending is complete.
    """
    with flask_app.app_context(): # Establish app context for DB operations in thread
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{current_time}] Thread started for campaign ID {db_campaign_id} ({len(recipients)} recipients).")

        # Update global in-memory status
        if db_campaign_id in campaign_sending_status:
            campaign_sending_status[db_campaign_id]["status"] = "Sending in progress..."

        results = bulk_send_emails(
            recipients=recipients,
            subject_template=subject,
            body_template_html=html_body,
            body_template_text=text_body,
            attachments=attachments,
            campaign_id=tracking_campaign_id, # This is the string campaign_id for sender.py
            link_url=link_url,
            num_threads=app.config.get('EMAIL_NUM_THREADS', 5), # Get from app config or default
            min_delay=app.config.get('EMAIL_MIN_DELAY', 1),
            max_delay=app.config.get('EMAIL_MAX_DELAY', 5)
        )

        campaign = Campaign.query.get(db_campaign_id)
        if campaign:
            campaign.total_sent = len(recipients) # Actual number attempted
            campaign.total_success = results.get("success", 0)
            campaign.total_failed = results.get("failed", 0)
            campaign.status = "Sent" if results.get("success",0) > 0 else "Failed"
            if results.get("failed", 0) > 0 and results.get("success", 0) == 0:
                campaign.status = "Completed with Errors"

            db.session.commit()
            print(f"Campaign {db_campaign_id} processing finished. Success: {campaign.total_success}, Failed: {campaign.total_failed}")
        else:
            print(f"Error: Campaign {db_campaign_id} not found after sending.")

        # Update or clear global status
        if db_campaign_id in campaign_sending_status:
            campaign_sending_status[db_campaign_id]["status"] = f"Completed. Success: {results.get('success',0)}, Failed: {results.get('failed',0)}"
            campaign_sending_status[db_campaign_id]["success_count"] = results.get('success',0)
            campaign_sending_status[db_campaign_id]["failed_count"] = results.get('failed',0)
            # Consider removing from campaign_sending_status after a while or if status is terminal


@app.route('/campaign/<int:campaign_id>/status')
@login_required
def campaign_status(campaign_id: int):
    """
    API endpoint polled by the frontend to get live status updates for a sending campaign.
    Returns JSON data from the in-memory `campaign_sending_status` or DB if not actively sending.
    """
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    # Prioritize in-memory status for active campaigns
    status_info = campaign_sending_status.get(campaign.id)

    if not status_info or campaign.status != "Sending":
        # If not actively sending or not in memory, fetch from DB as fallback
        status_info = {
            "name": campaign.name,
            "total": campaign.total_sent or 0,
            "sent_count": campaign.total_sent or 0, # This implies all attempted are 'sent' in a way
            "success_count": campaign.total_success or 0,
            "failed_count": campaign.total_failed or 0,
            "status": campaign.status,
            "source": "database"
        }
    else:
        status_info["source"] = "memory"

    return jsonify(status_info)

# --- Tracking Route ---
@app.route('/track/open', methods=['GET'])
def track_open():
    """
    Tracking pixel endpoint. Logs an email open event when the 1x1 pixel image
    is requested by an email client.
    """
    email = request.args.get('email')
    campaign_id_str = request.args.get('campaign_id', 'default') # From sender.py tracking pixel

    # Try to find the campaign by its ID (which was stringified from integer)
    campaign = None
    if campaign_id_str.isdigit():
        campaign = Campaign.query.get(int(campaign_id_str))

    # Log the open
    new_open = EmailTrack(
        recipient_email=email,
        campaign_id=campaign.id if campaign else None,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(new_open)
    db.session.commit()

    # Return a 1x1 transparent pixel
    # (Content of pixel can be pre-generated and served as static file for efficiency)
    from flask import make_response
    import base64
    pixel_gif_b64 = "R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==" # 1x1 transparent GIF
    pixel_data = base64.b64decode(pixel_gif_b64)
    response = make_response(pixel_data)
    response.headers['Content-Type'] = 'image/gif'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# --- Admin Routes ---
@app.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    """Displays the admin dashboard for user management and viewing all campaigns."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    all_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    # Further admin-specific stats can be added here
    return render_template('admin_dashboard.html', users=users, campaigns=all_campaigns)


@app.route('/admin/user/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
def toggle_admin_status(user_id: int):
    """Toggles the admin status of a user. Requires admin privileges."""
    if not current_user.is_admin:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('admin_dashboard'))

    user_to_modify = User.query.get_or_404(user_id)
    if user_to_modify.id == current_user.id and User.query.filter_by(is_admin=True).count() == 1:
        flash('Cannot remove admin status from the only admin user.', 'warning')
        return redirect(url_for('admin_dashboard'))

    user_to_modify.is_admin = not user_to_modify.is_admin
    db.session.commit()
    flash(f"User {user_to_modify.username}'s admin status updated.", 'success')
    return redirect(url_for('admin_dashboard'))


# --- Utility and Initialization Functions ---
def init_db():
    """
    Initializes the database: creates all tables based on models
    and creates a default admin user if one does not already exist.
    This function should be called once when setting up the application.
    """
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username='admin').first() is None:
            admin_user = User(username='admin', is_admin=True)
            admin_user.set_password('admin') # Default password, should be changed by the user.
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user 'admin' with password 'admin' created.")
        print("Database tables created/verified.")

# --- Main Execution ---
if __name__ == '__main__':
    # Initialize database (creates tables and default admin if necessary)
    init_db()

    # Configure application settings for email sending (can be moved to instance config)
    app.config['EMAIL_NUM_THREADS'] = 5     # Number of threads for sending emails
    app.config['EMAIL_MIN_DELAY'] = 1.0   # Minimum delay (seconds) between sends per thread
    app.config['EMAIL_MAX_DELAY'] = 3.0   # Maximum delay (seconds) between sends per thread

    # Ensure TRACKING_DOMAIN in sender.py matches the app's accessible URL for tracking to work.
    print(f"INFO: Email open tracking pixel URL is configured with TRACKING_DOMAIN: {TRACKING_DOMAIN}")
    print(f"INFO: Ensure this application is accessible at that domain for tracking to function.")
    print(f"INFO: Starting Flask development server on http://0.0.0.0:5000/")

    app.run(debug=True, host='0.0.0.0', port=5000) # debug=True is for development only.
