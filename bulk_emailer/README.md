# Bulk Emailer VictorV3

Bulk Emailer VictorV3 is a Python-based application for sending bulk emails with features for SMTP rotation, content randomization, performance, and a Flask-based web dashboard for management and real-time statistics.

## 🌟 Key Features

💌 **Bulk Email Sender (`sender.py`)**
*   Supports multiple SMTPs for load distribution.
*   Rotates: From Names, From Emails, Subjects.
*   Threaded sending for high performance.
*   Randomized delays between sends.
*   Tracks delivery status (Success / Fail) per campaign.
*   Embeds open tracking pixel.
*   Optional support for attachments (PDFs, images, etc.).
*   Supports HTML and Image letters (via HTML embedding or attachments).
*   Dynamic content using sender tags (e.g., `{{f_name}}`, `{{company}}`).

🌐 **Flask Admin Dashboard (`app.py`)**
*   Built with Flask + SQLite + Chart.js.
*   Accessible via web browser (default: `http://localhost:5000`).
*   Real-time stats: Total Sent, Success Count, Failed Count, Email Opens.
*   Pie Chart visualization for email status.
*   Admin and user login system with secure session-based authentication.
*   User roles (admin, user).

🔍 **Email Tracking**
*   Open tracking via a 1×1 pixel.
*   Logs each opened email by recipient, including IP and User-Agent.
*   Dashboard displays total opens for user's campaigns.

🛠️ **Setup & Execution**
*   Comes with `setup.bat` for 1-click setup on Windows (creates venv, installs requirements, initializes DB).
*   Requirements auto-installed on run via `setup.bat`.
*   Can be hosted on Windows RDP or local PC.

##  Prerequisites
*   Python 3.7+
*   `pip` (Python package installer)

## 🚀 Setup Instructions (Windows)

1.  **Download/Clone the Repository:**
    Ensure you have all the project files (`sender.py`, `app.py`, `requirements.txt`, `setup.bat`, `templates/` directory).

2.  **Run the Setup Script:**
    Navigate to the project directory in your command prompt and run:
    ```bash
    setup.bat
    ```
    This script will:
    *   Check for Python and pip.
    *   Create a virtual environment named `venv`.
    *   Activate the virtual environment.
    *   Install all necessary Python packages from `requirements.txt`.
    *   Initialize the SQLite database (`bulk_emailer.db`) and create a default admin user.

3.  **Configure SMTP Servers:**
    *   **THIS IS A CRUCIAL STEP FOR SENDING EMAILS.**
    *   Open `sender.py` in a text editor.
    *   Locate the `SMTP_SERVERS` list (around line 15).
    *   Add your SMTP server details. Example:
        ```python
        SMTP_SERVERS = [
            {'host': 'smtp.example.com', 'port': 587, 'username': 'your_email@example.com', 'password': 'your_password', 'use_tls': True},
            {'host': 'smtp.another.com', 'port': 465, 'username': 'another@another.com', 'password': 'another_password', 'use_tls': False}, # Example for SSL, sender.py defaults use_tls to True
            # Add more SMTP servers for rotation
        ]
        ```
    *   Update `FROM_EMAILS` in `sender.py` to include valid sender addresses that are authorized for the SMTP accounts you configured.
    *   You can also customize `FROM_NAMES` and `SUBJECTS` lists in `sender.py` as default templates/options.

## ▶️ Running the Application

1.  **Activate the Virtual Environment (if not already active or in a new terminal):**
    Navigate to the project directory in your command prompt:
    ```bash
    cd path\to\bulk_emailer
    venv\Scripts\activate.bat
    ```

2.  **Run the Flask Application:**
    ```bash
    python app.py
    ```

3.  **Access the Dashboard:**
    Open your web browser and go to `http://localhost:5000`.

4.  **Login:**
    *   The default admin credentials are:
        *   Username: `admin`
        *   Password: `admin`
    *   It is highly recommended to change the admin password after your first login (currently, this requires manual DB edit or a dedicated "change password" feature to be added). New users can register and will be standard users.

## 💻 Usage

*   **Dashboard:** View overall statistics of your email campaigns.
*   **Campaigns:**
    *   Create new email campaigns: define subject, HTML/text body, recipients (comma-separated), attachments, and a custom link for the `{{link}}` tag.
    *   Utilize various sender tags (listed in the campaign creation form) to personalize emails.
    *   View existing campaigns and their status.
    *   Send campaigns. The sending process runs in the background.
*   **Admin Dashboard (for admin users):**
    *   Manage users: View users and toggle their admin status.
    *   View all campaigns in the system.
    *   (Placeholder for global settings like SMTP configuration via UI).

## ⚙️ Sender Tags

The following tags can be used in the email subject and body (HTML & Text) to generate dynamic content:

*   `{{f_name}}`: Generates a fake name.
*   `{{f_email}}`: Generates a fake email address.
*   `{{f_company}}`: Generates a fake company name.
*   `{{bg_logo}}`: Tries to grab a company's logo using Clearbit (e.g., `https://logo.clearbit.com/example.com`). *Note: Clearbit usage might have limitations.*
*   `{{tmdate}}`: Gets tomorrow's date (YYYY-MM-DD).
*   `{{company}}`: Extracts the company name from the recipient's email address (e.g., "example" from "user@example.com").
*   `{{browser}}`: Generates a random browser name.
*   `{{country}}`: Generates a random country name.
*   `{{email}}`: The recipient's email address.
*   `{{email64}}`: A placeholder for a Base64 encoded email (currently generates a random Base64-like string).
*   `{{rstr}}`: Generates a random 8-character string.
*   `{{rnum}}`: Generates a random 6-digit number.
*   `{{time}}`: Gets the current time.
*   `{{user}}`: Extracts the user part from the recipient's email address (e.g., "user" from "user@example.com").
*   `{{link}}`: The URL you specify in the campaign's "Link URL" field.
*   `{{domain}}`: Extracts the domain part from the recipient's email address (e.g., "example.com" from "user@example.com").

## 🛠️ Potential Extensions & Future Development

*   **UI-based SMTP Configuration:** Allow admins to add/manage SMTP servers from the web interface.
*   **Advanced Campaign Scheduling:** Schedule campaigns to be sent at a specific date/time.
*   **Detailed Reporting:** More granular reports per campaign, including open rates, click rates (if link wrapping is added).
*   **Recipient List Management:** Upload recipient lists from CSV/TXT files; segment lists.
*   **A/B Testing:** Support for testing different subjects or email bodies.
*   **Link Click Tracking:** Wrap links in emails to track clicks.
*   **Enhanced Security:** Implement CSRF protection, two-factor authentication.
*   **Deployment:**
    *   Use a production-grade WSGI server like Gunicorn or uWSGI.
    *   Host with Nginx as a reverse proxy.
    *   Implement SSL/TLS using Let's Encrypt.
*   **EXE Compilation:** Package the application as a standalone executable using PyInstaller or similar tools.

## 📝 Notes

*   The application uses SQLite as its database, which creates a file named `bulk_emailer.db` in the project directory.
*   Email sending is performed in background threads. Check the console output of `app.py` for sending logs and potential errors from `sender.py`.
*   The open tracking pixel is a basic implementation. Some email clients or ad-blockers might block it.
*   Ensure the `TRACKING_DOMAIN` in `sender.py` (currently `http://localhost:5000`) matches the actual URL where your Flask app is accessible if you deploy it elsewhere.

---

This project is for educational and illustrative purposes. When sending bulk emails, always comply with anti-spam laws and regulations (e.g., CAN-SPAM, GDPR). Ensure you have consent from recipients.
