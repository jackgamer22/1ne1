"""
Flask Web Application for Bulk Emailer VictorV3

This application provides a web interface for managing email campaigns,
viewing statistics, and user authentication. It uses Flask, SQLAlchemy for
database interactions, and Flask-Login for session management.
It interacts with sender.py for the email sending logic.

Refactored to use the application factory pattern (create_app).
"""
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import threading
import base64

# Import sender functionalities (assuming sender.py is in the same directory)
try:
    from sender import bulk_send_emails, SMTP_SERVERS as SENDER_SMTP_SERVERS, \
                       FROM_NAMES as SENDER_FROM_NAMES, FROM_EMAILS as SENDER_FROM_EMAILS, \
                       SUBJECTS as SENDER_SUBJECTS, TRACKING_DOMAIN as SENDER_TRACKING_DOMAIN
except ImportError:
    print("CRITICAL: sender.py not found or contains errors. App may not function correctly.")
    def bulk_send_emails(*args, **kwargs): return {"success": 0, "failed": 0, "details": []}
    SENDER_SMTP_SERVERS, SENDER_FROM_NAMES, SENDER_FROM_EMAILS, SENDER_SUBJECTS, SENDER_TRACKING_DOMAIN = [], [], [], [], "http://localhost:5000"

# --- Database and Login Manager Instances (Initialize in create_app) ---
db = SQLAlchemy()
login_manager = LoginManager()

# --- Models ---
# Defined globally, but SQLAlchemy engine is configured in create_app via db.init_app(app)
class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Campaign(db.Model):
    """Campaign model to store details of an email campaign."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, default=lambda: f"Campaign_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    subject = db.Column(db.String(255), nullable=False)
    html_body = db.Column(db.Text, nullable=False)
    text_body = db.Column(db.Text, nullable=True)
    recipients = db.Column(db.Text, nullable=False)
    attachments_json = db.Column(db.Text, nullable=True)
    link_url = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('campaigns', lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Pending")
    total_sent = db.Column(db.Integer, default=0)
    total_success = db.Column(db.Integer, default=0)
    total_failed = db.Column(db.Integer, default=0)

class EmailTrack(db.Model):
    """EmailTrack model to log email open events."""
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=True)
    recipient_email = db.Column(db.String(255), nullable=False, index=True)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    campaign = db.relationship('Campaign', backref=db.backref('opens', lazy='dynamic'))

# --- Global In-Memory State (Consider alternatives for production) ---
campaign_sending_status = {} # campaign_id: {"name": str, "total": int, ...}


# --- Application Factory ---
def create_app(config_dict: dict):
    """
    Factory function to create and configure the Flask application.
    """
    app = Flask(__name__, template_folder='templates')
    app.config.from_mapping(config_dict) # Load config from argument

    # Configure UPLOAD_FOLDER (create if it doesn't exist)
    app.config.setdefault('UPLOAD_FOLDER', 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Configure Database URI if not already set by environment
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///bulk_emailer.db')
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)


    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login' # Route for @login_required

    @login_manager.user_loader
    def load_user(user_id: str) -> User:
        return User.query.get(int(user_id))

    # --- Routes (defined within create_app to have access to 'app') ---
    @app.route('/login', methods=['GET', 'POST'])
    def login():
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
        logout_user()
        flash('Logged out successfully.', 'success')
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists.', 'warning')
                return redirect(url_for('register'))

            new_user = User(username=username)
            new_user.set_password(password)
            if User.query.count() == 0: # First user is admin
                new_user.is_admin = True
                flash('Admin user registered successfully! Please log in.', 'success')
            else:
                flash('User registered successfully! Please log in.', 'success')

            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/')
    @login_required
    def index():
        return redirect(url_for('dashboard'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        total_campaigns = Campaign.query.filter_by(user_id=current_user.id).count()
        user_campaigns = Campaign.query.filter_by(user_id=current_user.id).all()
        total_sent_overall = sum(c.total_sent or 0 for c in user_campaigns)
        total_success_overall = sum(c.total_success or 0 for c in user_campaigns)
        total_failed_overall = sum(c.total_failed or 0 for c in user_campaigns)
        total_opens_overall = db.session.query(db.func.count(EmailTrack.id))\
                                .join(Campaign)\
                                .filter(Campaign.user_id == current_user.id)\
                                .scalar() or 0
        chart_data = {
            "labels": ["Success", "Failed", "Not Yet Sent/Accounted"],
            "datasets": [{
                "label": "Email Status",
                "data": [
                    total_success_overall,
                    total_failed_overall,
                    max(0, total_sent_overall - (total_success_overall + total_failed_overall))
                ],
                "backgroundColor": ['rgba(75, 192, 192, 0.7)', 'rgba(255, 99, 132, 0.7)', 'rgba(201, 203, 207, 0.7)'],
                "borderColor": ['rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)', 'rgba(201, 203, 207, 1)'],
                "borderWidth": 1
            }]
        }
        recent_campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(Campaign.created_at.desc()).limit(5).all()
        return render_template('dashboard.html',
                               total_campaigns=total_campaigns, total_sent=total_sent_overall,
                               total_success=total_success_overall, total_failed=total_failed_overall,
                               total_opens=total_opens_overall, chart_data=json.dumps(chart_data),
                               recent_campaigns=recent_campaigns, campaign_sending_status=campaign_sending_status)

    @app.route('/campaigns', methods=['GET', 'POST'])
    @login_required
    def manage_campaigns():
        if request.method == 'POST':
            name = request.form.get('name') or f"Campaign_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            subject = request.form['subject']
            html_body = request.form['html_body']
            text_body = request.form.get('text_body', '')
            recipients_str = request.form['recipients']
            link_url = request.form.get('link_url', '')
            uploaded_files_info = []
            if 'attachments' in request.files:
                files = request.files.getlist('attachments')
                for file_item in files:
                    if file_item and file_item.filename:
                        filename = secure_filename(file_item.filename)
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file_item.save(filepath)
                        uploaded_files_info.append({'path': filepath, 'filename': filename, 'type': file_item.mimetype})

            new_campaign = Campaign(name=name, subject=subject, html_body=html_body, text_body=text_body,
                                    recipients=recipients_str,
                                    attachments_json=json.dumps(uploaded_files_info) if uploaded_files_info else None,
                                    link_url=link_url, user_id=current_user.id, status="Pending")
            db.session.add(new_campaign)
            db.session.commit()
            flash(f'Campaign "{name}" created successfully!', 'success')
            return redirect(url_for('manage_campaigns'))

        campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(Campaign.created_at.desc()).all()
        # Use SENDER_ variables for defaults if app config doesn't override them
        return render_template('campaigns.html', campaigns=campaigns,
                                smtp_configured=bool(app.config.get('SENDER_SMTP_SERVERS', SENDER_SMTP_SERVERS)),
                                from_names=app.config.get('SENDER_FROM_NAMES', SENDER_FROM_NAMES),
                                from_emails=app.config.get('SENDER_FROM_EMAILS', SENDER_FROM_EMAILS),
                                subjects=app.config.get('SENDER_SUBJECTS', SENDER_SUBJECTS))

    @app.route('/campaign/<int:campaign_id>/send', methods=['POST'])
    @login_required
    def send_campaign(campaign_id: int):
        campaign = Campaign.query.get_or_404(campaign_id)
        if campaign.user_id != current_user.id and not current_user.is_admin:
            flash('You do not have permission to send this campaign.', 'danger')
            return redirect(url_for('manage_campaigns'))

        active_smtp_servers = app.config.get('SENDER_SMTP_SERVERS', SENDER_SMTP_SERVERS)
        if not active_smtp_servers:
            flash('SMTP servers are not configured. Cannot send emails.', 'danger')
            return redirect(url_for('manage_campaigns'))

        if campaign.status == "Sending":
            flash(f'Campaign "{campaign.name}" is already being sent.', 'warning')
            return redirect(url_for('manage_campaigns'))

        recipients_list = [email.strip() for email in campaign.recipients.split(',') if email.strip()]
        if not recipients_list:
            flash('No recipients specified for this campaign.', 'danger')
            campaign.status = "Failed"; db.session.commit()
            return redirect(url_for('manage_campaigns'))

        attachments = json.loads(campaign.attachments_json) if campaign.attachments_json else []
        campaign.status = "Sending"
        campaign.total_sent = len(recipients_list)
        campaign.total_success = 0; campaign.total_failed = 0
        db.session.commit()

        campaign_sending_status[campaign.id] = {
            "name": campaign.name, "total": len(recipients_list), "sent_count": 0,
            "success_count": 0, "failed_count": 0, "status": "Initializing..."}

        # Pass the current app instance to the thread context
        thread_app = app._get_current_object() # Get current app proxy's underlying object

        thread = threading.Thread(target=execute_sending_logic, args=(
            thread_app, campaign.id, recipients_list, campaign.subject, campaign.html_body,
            campaign.text_body, attachments, str(campaign.id), campaign.link_url
        ))
        thread.daemon = True
        thread.start()
        flash(f'Campaign "{campaign.name}" sending process initiated.', 'info')
        return redirect(url_for('dashboard'))

    @app.route('/campaign/<int:campaign_id>/status')
    @login_required
    def campaign_status_route(campaign_id: int): # Renamed to avoid conflict if 'campaign_status' is used as var
        campaign = Campaign.query.get_or_404(campaign_id)
        if campaign.user_id != current_user.id and not current_user.is_admin:
            return jsonify({"error": "Unauthorized"}), 403

        status_info_mem = campaign_sending_status.get(campaign.id)
        if not status_info_mem or campaign.status != "Sending":
            status_info = {"name": campaign.name, "total": campaign.total_sent or 0,
                           "sent_count": campaign.total_sent or 0,
                           "success_count": campaign.total_success or 0,
                           "failed_count": campaign.total_failed or 0,
                           "status": campaign.status, "source": "database"}
        else:
            status_info = status_info_mem
            status_info["source"] = "memory"
        return jsonify(status_info)

    @app.route('/track/open', methods=['GET'])
    def track_open():
        email = request.args.get('email')
        campaign_id_str = request.args.get('campaign_id', 'default')
        campaign_obj = None
        if campaign_id_str.isdigit():
            campaign_obj = Campaign.query.get(int(campaign_id_str))

        new_open = EmailTrack(recipient_email=email, campaign_id=campaign_obj.id if campaign_obj else None,
                              ip_address=request.remote_addr, user_agent=request.user_agent.string)
        db.session.add(new_open)
        db.session.commit()

        pixel_gif_b64 = "R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
        pixel_data = base64.b64decode(pixel_gif_b64)
        response = make_response(pixel_data)
        response.headers['Content-Type'] = 'image/gif'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'; response.headers['Expires'] = '0'
        return response

    @app.route('/admin', methods=['GET'])
    @login_required
    def admin_dashboard():
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        users = User.query.all()
        all_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
        # TRACKING_DOMAIN will now come from app.config
        current_tracking_domain = app.config.get('SENDER_TRACKING_DOMAIN', SENDER_TRACKING_DOMAIN)
        return render_template('admin_dashboard.html', users=users, campaigns=all_campaigns, TRACKING_DOMAIN=current_tracking_domain)

    @app.route('/admin/user/<int:user_id>/toggle_admin', methods=['POST'])
    @login_required
    def toggle_admin_status(user_id: int):
        if not current_user.is_admin:
            flash('Unauthorized.', 'danger'); return redirect(url_for('admin_dashboard'))
        user_to_modify = User.query.get_or_404(user_id)
        if user_to_modify.id == current_user.id and User.query.filter_by(is_admin=True).count() == 1:
            flash('Cannot remove admin status from the only admin user.', 'warning')
        else:
            user_to_modify.is_admin = not user_to_modify.is_admin
            db.session.commit()
            flash(f"User {user_to_modify.username}'s admin status updated.", 'success')
        return redirect(url_for('admin_dashboard'))

    # --- Utility function for DB initialization ---
    # This needs to be callable after app is created, so it's defined here
    # but typically called from the main script block or a separate CLI command.
    def init_db_command():
        """Initializes the database and creates a default admin user."""
        with app.app_context(): # app context is crucial here
            db.create_all()
            if User.query.filter_by(username='admin').first() is None:
                admin_user = User(username='admin', is_admin=True)
                admin_user.set_password(app.config.get('DEFAULT_ADMIN_PASSWORD', 'admin'))
                db.session.add(admin_user)
                db.session.commit()
                print(f"Default admin user 'admin' with default password created.")
            print("Database tables created/verified.")

    # Register as a CLI command if desired, or call directly
    @app.cli.command("init-db")
    def init_db_cli():
        """CLI command to initialize the database."""
        init_db_command()
        print("Database initialized via CLI.")

    return app

# --- Email Sending Logic (Thread Worker) ---
def execute_sending_logic(flask_app_instance, db_campaign_id, recipients, subject, html_body,
                          text_body, attachments, tracking_campaign_id, link_url):
    """
    Wrapper function to run email sending logic in a separate thread.
    Requires the Flask app context for DB operations.
    """
    with flask_app_instance.app_context(): # Use the passed app instance for context
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{current_time}] Thread started for campaign ID {db_campaign_id} ({len(recipients)} recipients).")

        if db_campaign_id in campaign_sending_status:
            campaign_sending_status[db_campaign_id]["status"] = "Sending in progress..."

        # Get email sending params from app config (passed from create_app)
        num_threads = flask_app_instance.config.get('EMAIL_NUM_THREADS', 5)
        min_delay = flask_app_instance.config.get('EMAIL_MIN_DELAY', 1.0)
        max_delay = flask_app_instance.config.get('EMAIL_MAX_DELAY', 3.0)

        # Update sender.py's global config if necessary, or pass them directly
        # For now, assuming sender.py will use its own globals or they are updated elsewhere
        # A better way would be to pass SENDER_SMTP_SERVERS etc. to bulk_send_emails if possible
        # Or, sender.py could have a configure() function called from create_app

        # Ensure sender.py uses the app's configured SMTP servers, not its own hardcoded ones
        # This is a bit of a hack; ideally sender.py's functions would take these as args
        global SENDER_SMTP_SERVERS, SENDER_FROM_NAMES, SENDER_FROM_EMAILS, SENDER_SUBJECTS, SENDER_TRACKING_DOMAIN
        SENDER_SMTP_SERVERS = flask_app_instance.config.get('SENDER_SMTP_SERVERS', SENDER_SMTP_SERVERS)
        SENDER_FROM_NAMES = flask_app_instance.config.get('SENDER_FROM_NAMES', SENDER_FROM_NAMES)
        SENDER_FROM_EMAILS = flask_app_instance.config.get('SENDER_FROM_EMAILS', SENDER_FROM_EMAILS)
        SENDER_SUBJECTS = flask_app_instance.config.get('SENDER_SUBJECTS', SENDER_SUBJECTS)
        SENDER_TRACKING_DOMAIN = flask_app_instance.config.get('SENDER_TRACKING_DOMAIN', SENDER_TRACKING_DOMAIN)


        results = bulk_send_emails(
            recipients=recipients, subject_template=subject, body_template_html=html_body,
            body_template_text=text_body, attachments=attachments, campaign_id=tracking_campaign_id,
            link_url=link_url, num_threads=num_threads, min_delay=min_delay, max_delay=max_delay
        )

        campaign = Campaign.query.get(db_campaign_id)
        if campaign:
            campaign.total_sent = len(recipients)
            campaign.total_success = results.get("success", 0)
            campaign.total_failed = results.get("failed", 0)
            if results.get("failed", 0) > 0 and results.get("success", 0) == 0 and len(recipients) > 0 :
                 campaign.status = "Failed"
            elif results.get("success",0) > 0 :
                 campaign.status = "Sent"
            else: # No successes, no failures, possibly no recipients or other issue
                 campaign.status = "Completed with Issues"

            db.session.commit()
            print(f"Campaign {db_campaign_id} processing finished. Status: {campaign.status}, Success: {campaign.total_success}, Failed: {campaign.total_failed}")
        else:
            print(f"Error: Campaign {db_campaign_id} not found after sending.")

        if db_campaign_id in campaign_sending_status:
            campaign_sending_status[db_campaign_id]["status"] = f"Completed. Success: {results.get('success',0)}, Failed: {results.get('failed',0)}"
            campaign_sending_status[db_campaign_id]["success_count"] = results.get('success',0)
            campaign_sending_status[db_campaign_id]["failed_count"] = results.get('failed',0)


# --- Configuration Loading ---
def get_config():
    """Load configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    # Default values from sender.py can be used if not overridden by env vars
    config = {
        'ENV': env,
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev_secret_key_!@#$%^&*()_BULK_EMAILER'),
        'DEBUG': env != 'production',
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///bulk_emailer.db'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'UPLOAD_FOLDER': os.environ.get('UPLOAD_FOLDER', 'uploads'),
        'DEFAULT_ADMIN_PASSWORD': os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin'),

        # Email sending configuration (can be overridden by environment variables)
        'EMAIL_NUM_THREADS': int(os.environ.get('EMAIL_NUM_THREADS', '5')),
        'EMAIL_MIN_DELAY': float(os.environ.get('EMAIL_MIN_DELAY', '1.0')),
        'EMAIL_MAX_DELAY': float(os.environ.get('EMAIL_MAX_DELAY', '3.0')),

        # SMTP and sender related configurations
        # These will override sender.py's globals if set, otherwise sender.py's defaults are used.
        # For a cleaner approach, sender.py functions should accept these as parameters.
        'SENDER_SMTP_SERVERS': json.loads(os.environ.get('SENDER_SMTP_SERVERS_JSON', '[]')) or SENDER_SMTP_SERVERS,
        'SENDER_FROM_NAMES': json.loads(os.environ.get('SENDER_FROM_NAMES_JSON', '[]')) or SENDER_FROM_NAMES,
        'SENDER_FROM_EMAILS': json.loads(os.environ.get('SENDER_FROM_EMAILS_JSON', '[]')) or SENDER_FROM_EMAILS,
        'SENDER_SUBJECTS': json.loads(os.environ.get('SENDER_SUBJECTS_JSON', '[]')) or SENDER_SUBJECTS,
        'SENDER_TRACKING_DOMAIN': os.environ.get('SENDER_TRACKING_DOMAIN', SENDER_TRACKING_DOMAIN),
    }
    return config

# --- Main Execution ---
if __name__ == '__main__':
    app_config = get_config()
    app = create_app(app_config)

    # Initialize DB through app context if not using CLI command 'flask init-db'
    # This ensures it runs when 'python app.py' is executed directly.
    with app.app_context():
        # Check if DB needs initialization (e.g. if file doesn't exist for sqlite)
        # A more robust check might be to see if tables exist.
        db_path_str = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///') and not os.path.exists(db_path_str):
            print(f"SQLite database not found at {db_path_str}. Initializing...")
            db.create_all() # Create tables if they don't exist
            if User.query.filter_by(username='admin').first() is None:
                admin_user = User(username='admin', is_admin=True)
                admin_user.set_password(app.config.get('DEFAULT_ADMIN_PASSWORD', 'admin'))
                db.session.add(admin_user)
                db.session.commit()
                print(f"Default admin user 'admin' created.")
            print("Database initialized.")
        else:
             # Ensure tables exist even if DB file exists
            db.create_all()
            print("Database tables verified.")


    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Bulk Email System on http://0.0.0.0:{port}")
    print(f"Environment: {app.config['ENV']}")
    print(f"Debug mode: {'Enabled' if app.config['DEBUG'] else 'Disabled'}")

    # The `SENDER_...` configurations loaded in `get_config()` will be available in `app.config`.
    # The `execute_sending_logic` function has been updated to use these from `flask_app_instance.config`.
    # However, for `sender.py` to pick these up if its functions are called directly
    # or if it relies on its own globals, those globals in sender.py need to be updated.
    # The current `execute_sending_logic` attempts to update sender.py's globals, which is a workaround.

    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
