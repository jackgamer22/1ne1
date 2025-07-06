"""
Core Email Sending Logic for Bulk Emailer VictorV3

This module handles the actual sending of emails, including:
- SMTP server management and rotation.
- Email content generation with dynamic tag replacement.
- Support for HTML, plain text, and attachments.
- Open tracking pixel generation.
- Threaded sending for performance.
- Randomized delays to mimic human behavior.
"""
import smtplib
import random
import time
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from faker import Faker
import re
from urllib.parse import quote

# Initialize Faker for generating fake data
fake = Faker()

# --- Configuration Variables ---
# These are typically loaded from a configuration file or a UI in a full application.
# For this version, they are hardcoded here but intended to be managed by the Flask app eventually.

SMTP_SERVERS = [
    # Example: {'host': 'smtp.example.com', 'port': 587, 'username': 'user', 'password': 'password', 'use_tls': True}
    # {'host': 'smtp.gmail.com', 'port': 465, 'username': 'yourgmail@gmail.com', 'password': 'yourgmailapppassword', 'use_tls': False} # For SSL
]
"""List of SMTP server configurations. Each configuration is a dictionary."""

FROM_NAMES = ["Tech Support", "Customer Service", "Newsletter Team", "Promotions"]
"""List of 'From' names to be rotated during sending."""

FROM_EMAILS = ["noreply@yourdomain.com", "support@yourdomain.com"] # These should be valid senders for your SMTP_SERVERS
"""List of 'From' email addresses to be rotated. Should align with SMTP server authorization."""

SUBJECTS = ["A Special Offer Just For You, {{f_name}}!", "Important Account Update", "Your Weekly Digest is Here"]
"""List of email subject lines to be rotated. Sender tags can be used here."""

TRACKING_DOMAIN = "http://localhost:5000" # Should match the domain where app.py is running
"""Base URL for the open tracking pixel. Must point to the Flask app's tracking endpoint."""


# --- Helper Functions ---

def get_random_smtp():
    """Selects a random SMTP server from the list."""
    if not SMTP_SERVERS:
        raise ValueError("No SMTP servers configured.")
    return random.choice(SMTP_SERVERS)

def get_random_from_name():
    """Selects a random 'From Name'."""
    return random.choice(FROM_NAMES) if FROM_NAMES else "NoName"

def get_random_from_email():
    """Selects a random 'From Email'."""
    return random.choice(FROM_EMAILS) if FROM_EMAILS else "noreply@default.com"

def get_random_subject():
    """Selects a random subject line."""
    return random.choice(SUBJECTS) if SUBJECTS else "Default Subject"

def generate_tracking_pixel(recipient_email, campaign_id="default"):
    """Generates an HTML tracking pixel."""
    encoded_email = quote(recipient_email)
    return f'<img src="{TRACKING_DOMAIN}/track/open?email={encoded_email}&campaign_id={campaign_id}" width="1" height="1" alt="">'

def replace_sender_tags(content, recipient_email, link_url=""):
    """Replaces sender tags in the email content."""
    company_match = re.search(r'@([\w.-]+)', recipient_email)
    company_name_from_email = company_match.group(1).split('.')[0] if company_match else "Valued Customer"
    user_from_email = recipient_email.split('@')[0]
    domain_from_email = recipient_email.split('@')[1] if '@' in recipient_email else "example.com"

    replacements = {
        "{{f_name}}": fake.name(),
        "{{f_email}}": fake.email(),
        "{{f_company}}": fake.company(),
        "{{bg_logo}}": f"https://logo.clearbit.com/{domain_from_email}", # Placeholder, Clearbit might require API key
        "{{tmdate}}": (fake.date_time_this_month(before_now=False, after_now=True)).strftime('%Y-%m-%d'),
        "{{company}}": company_name_from_email,
        "{{browser}}": fake.user_agent().split('/')[0], # Simplified browser
        "{{country}}": fake.country(), # Note: Original tag was {{country}}, assuming it meant fake country.
        "{{email}}": recipient_email,
        "{{email64}}": fake.pystr_format(string_format="??????##", letters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/="), # Simplified base64-like
        "{{rstr}}": fake.pystr(min_chars=8, max_chars=8),
        "{{rnum}}": str(fake.random_number(digits=6, fix_len=True)),
        "{{time}}": fake.time(),
        "{{user}}": user_from_email,
        "{{link}}": link_url,
        "{{domain}}": domain_from_email,
    }
    for tag, value in replacements.items():
        content = content.replace(tag, str(value))
    return content

# --- Core Email Sending Function ---
def send_email(recipient_email: str, subject_template: str, body_template_html: str,
               body_template_text: str = None, attachments: list = None,
               campaign_id: str = "default", link_url: str = "") -> tuple[bool, str]:
    """
    Sends a single email with specified parameters, including tag replacement,
    attachments, and tracking pixel.

    Args:
        recipient_email (str): The email address of the recipient.
        subject_template (str): The subject line, possibly with tags.
        body_template_html (str): The HTML body of the email, possibly with tags.
        body_template_text (str, optional): The plain text body. Defaults to None.
        attachments (list, optional): List of attachment paths.
                                      Each item can be a string (filepath) or a dict
                                      {'path': 'filepath', 'type': 'pdf'/'image', 'filename': 'custom_name.ext'}
        campaign_id (str, optional): Identifier for the campaign.
        link_url (str, optional): URL to be inserted for the {{link}} tag.

    Returns:
        tuple: (bool, str) indicating (success, message/error)
    """
    try:
        smtp_config = get_random_smtp()
        from_name = get_random_from_name()
        from_email = get_random_from_email() # This should ideally be tied to the chosen SMTP's allowed sender

        # Replace sender tags
        final_subject = replace_sender_tags(subject_template, recipient_email, link_url)
        final_body_html = replace_sender_tags(body_template_html, recipient_email, link_url)
        if body_template_text:
            final_body_text = replace_sender_tags(body_template_text, recipient_email, link_url)
        else:
            # Basic conversion from HTML to text if no text body provided
            # This is a very naive conversion and can be improved with libraries like html2text
            temp_text = re.sub('<[^<]+?>', '', final_body_html) # Strip HTML tags
            final_body_text = re.sub(r'\s+', ' ', temp_text).strip() # Normalize whitespace


        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = final_subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = recipient_email

        # Attach plain text and HTML parts
        if final_body_text:
            msg.attach(MIMEText(final_body_text, 'plain'))
        msg.attach(MIMEText(final_body_html, 'html'))

        # Embed tracking pixel
        tracking_pixel_html = generate_tracking_pixel(recipient_email, campaign_id)
        msg.attach(MIMEText(tracking_pixel_html, 'html')) # Add it to the HTML part

        # Add attachments
        if attachments:
            for att_info in attachments:
                filepath = None
                custom_filename = None
                attachment_type = None # 'pdf', 'image', 'other'

                if isinstance(att_info, str):
                    filepath = att_info
                    custom_filename = filepath.split('/')[-1].split('\\')[-1] # Get base filename
                elif isinstance(att_info, dict):
                    filepath = att_info.get('path')
                    custom_filename = att_info.get('filename', filepath.split('/')[-1].split('\\')[-1] if filepath else None)
                    attachment_type = att_info.get('type')

                if not filepath:
                    print(f"Warning: Attachment path not provided for {att_info}")
                    continue

                try:
                    with open(filepath, 'rb') as f_att:
                        if attachment_type == 'pdf' or filepath.lower().endswith('.pdf'):
                            part = MIMEApplication(f_att.read(), Name=custom_filename)
                            part['Content-Disposition'] = f'attachment; filename="{custom_filename}"'
                            msg.attach(part)
                        elif attachment_type == 'image' or any(filepath.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                            part = MIMEImage(f_att.read(), name=custom_filename)
                            part['Content-Disposition'] = f'attachment; filename="{custom_filename}"'
                            msg.attach(part)
                        else: # Generic binary attachment
                            part = MIMEApplication(f_att.read(), Name=custom_filename, _subtype="octet-stream")
                            part['Content-Disposition'] = f'attachment; filename="{custom_filename}"'
                            msg.attach(part)
                except FileNotFoundError:
                    return False, f"Attachment file not found: {filepath}"
                except Exception as e_att:
                    return False, f"Error attaching file {filepath}: {e_att}"


        # Send the email
        with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
            if smtp_config.get('use_tls', True): # Default to TLS
                server.starttls()
            if smtp_config.get('username') and smtp_config.get('password'):
                server.login(smtp_config['username'], smtp_config['password'])
            server.sendmail(from_email, recipient_email, msg.as_string())

        return True, f"Email sent to {recipient_email} via {smtp_config['host']}"

    except smtplib.SMTPAuthenticationError as e:
        return False, f"SMTP Authentication Error for {smtp_config.get('host')}: {e}"
    except smtplib.SMTPServerDisconnected as e:
        return False, f"SMTP Server Disconnected for {smtp_config.get('host')}: {e}. Check port or network."
    except smtplib.SMTPConnectError as e:
        return False, f"SMTP Connection Error for {smtp_config.get('host')}: {e}. Check host/port."
    except smtplib.SMTPException as e:
        return False, f"SMTP Error for {smtp_config.get('host')}: {e}"
    except FileNotFoundError as e: # Catching FileNotFoundError for attachments here as a fallback
        return False, str(e)
    except Exception as e:
        return False, f"General error sending email: {e}"

# --- Threaded Sending Logic ---
email_status = {"success": 0, "failed": 0, "details": []} # Global dictionary to track status from threads
email_status_lock = threading.Lock() # Lock for safe concurrent access to email_status

def worker(recipient_list: list[str], subject_template: str, body_template_html: str,
           body_template_text: str, attachments: list, campaign_id: str,
           link_url: str, min_delay: float, max_delay: float):
    """
    Worker function executed by each sender thread.
    Iterates through a portion of the recipient list, sends emails,
    and updates the shared email_status dictionary.
    """
    global email_status
    for recipient in recipient_list:
        success, message = send_email(
            recipient_email=recipient,
            subject_template=subject_template,
            body_template_html=body_template_html,
            body_template_text=body_template_text,
            attachments=attachments,
            campaign_id=campaign_id,
            link_url=link_url
        )
        with email_status_lock:
            if success:
                email_status["success"] += 1
            else:
                email_status["failed"] += 1
            email_status["details"].append({"email": recipient, "status": "Success" if success else "Fail", "message": message})

        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

def bulk_send_emails(recipients: list[str], subject_template: str, body_template_html: str,
                     body_template_text: str = None, attachments: list = None,
                     campaign_id: str = "default", link_url: str = "",
                     num_threads: int = 5, min_delay: float = 1.0, max_delay: float = 5.0) -> dict:
    """
    Manages the bulk email sending process using multiple threads.
    It divides the recipient list among worker threads and collects results.

    Args:
        recipients (list): List of recipient email addresses.
        subject_template (str): Subject line template.
        body_template_html (str): HTML body template.
        body_template_text (str, optional): Plain text body template.
        attachments (list, optional): List of attachment file paths or dicts.
        campaign_id (str, optional): Campaign identifier.
        link_url (str, optional): URL for the {{link}} tag.
        num_threads (int, optional): Number of concurrent sending threads.
        min_delay (float, optional): Minimum delay between sends per thread (seconds).
        max_delay (float, optional): Maximum delay between sends per thread (seconds).

    Returns:
        dict: A dictionary containing the status of the bulk send.
    """
    global email_status
    email_status = {"success": 0, "failed": 0, "details": []} # Reset status

    if not SMTP_SERVERS:
        print("Error: No SMTP servers configured in sender.py:SMTP_SERVERS.")
        return {"success": 0, "failed": len(recipients), "details": [{"email": r, "status": "Fail", "message": "No SMTP servers configured"} for r in recipients]}

    threads = []
    recipient_chunks = [recipients[i::num_threads] for i in range(num_threads)]

    print(f"Starting bulk send with {num_threads} threads...")

    for i in range(num_threads):
        if not recipient_chunks[i]: # Skip creating thread if chunk is empty
            continue
        thread = threading.Thread(
            target=worker,
            args=(
                recipient_chunks[i],
                subject_template,
                body_template_html,
                body_template_text,
                attachments,
                campaign_id,
                link_url,
                min_delay,
                max_delay
            )
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print(f"Bulk send complete. Success: {email_status['success']}, Failed: {email_status['failed']}")
    return email_status

# --- Example Usage (for testing sender.py directly) ---
if __name__ == "__main__":
    # IMPORTANT: Configure SMTP_SERVERS before running!
    # Example:
    SMTP_SERVERS = [
         {'host': 'smtp.mailtrap.io', 'port': 2525, 'username': 'YOUR_MAILTRAP_USERNAME', 'password': 'YOUR_MAILTRAP_PASSWORD', 'use_tls': True},
        # Add more real SMTP servers here for actual sending
    ]
    # FROM_EMAILS should be emails you are authorized to send from via the configured SMTPs
    FROM_EMAILS = ["testsender@example.com"]


    if not SMTP_SERVERS or 'YOUR_MAILTRAP_USERNAME' in SMTP_SERVERS[0].get('username', ''):
        print("="*50)
        print("WARNING: SMTP_SERVERS are not configured or are using placeholder values.")
        print("Please edit sender.py and add your actual SMTP server details to the SMTP_SERVERS list.")
        print("You can use a service like Mailtrap.io for safe testing.")
        print("Example SMTP_SERVERS format:")
        print("""
SMTP_SERVERS = [
    {'host': 'smtp.example.com', 'port': 587, 'username': 'your_email@example.com', 'password': 'your_password', 'use_tls': True},
    {'host': 'smtp.another.com', 'port': 465, 'username': 'another_email@another.com', 'password': 'another_password', 'use_tls': False} # Example for SSL
]
        """)
        print("="*50)
        # Create dummy files for attachment testing
        with open("sample.pdf", "w") as f: f.write("This is a dummy PDF.")
        with open("sample.jpg", "w") as f: f.write("This is a dummy JPG.")


    # Test recipients
    test_recipients = [fake.email() for _ in range(3)] # Generate 3 fake emails for testing
    test_recipients.append("testuser@example.com") # Add a more readable one

    # Test email content
    test_subject = "Test Email from Bulk Sender {{rnum}}"
    test_html_body = """
    <h1>Hello {{f_name}} at {{company}}!</h1>
    <p>This is a test email sent at {{time}}.</p>
    <p>Your email is {{email}}, and your base64 email is {{email64}}.</p>
    <p>Tomorrow's date is {{tmdate}}.</p>
    <p>We detected you might be using {{browser}} from {{country}}.</p>
    <p>Here is a random string: {{rstr}} and a random number: {{rnum}}.</p>
    <p>Click this link: <a href="{{link}}">Special Offer</a></p>
    <p>Your domain is {{domain}} and user is {{user}}.</p>
    <p><img src="{{bg_logo}}" alt="Company Logo"></p>
    <p>This is an image letter part: <img src="cid:image1" alt="Embedded Image"></p>
    """
    # For embedding image directly in HTML (cid)
    # You'd need to modify send_email to handle cid images if you want them separate from attachments
    # For now, {{bg_logo}} is an external link, and actual image attachments are separate.

    test_text_body = "Hello {{f_name}},\nThis is a plain text version of the test email.\nLink: {{link}}"

    # Test attachments (provide paths to actual files or create dummy ones)
    test_attachments = [
        "sample.pdf", # Simple path
        {"path": "sample.jpg", "type": "image", "filename": "photo_test.jpg"},
        # {"path": "path/to/your/image_letter.png", "type": "image"} # For image letter as attachment
    ]


    print(f"Sending test emails to: {test_recipients}")
    results = bulk_send_emails(
        recipients=test_recipients,
        subject_template=test_subject,
        body_template_html=test_html_body,
        body_template_text=test_text_body,
        attachments=test_attachments,
        campaign_id="test_campaign_01",
        link_url="http://example.com/offer123",
        num_threads=2,
        min_delay=0.5,
        max_delay=1.5
    )

    print("\n--- Sending Results ---")
    for detail in results.get("details", []):
        print(f"Email: {detail['email']}, Status: {detail['status']}, Info: {detail['message']}")
    print(f"\nTotal Success: {results.get('success',0)}, Total Failed: {results.get('failed',0)}")

    # Clean up dummy files
    if 'sample.pdf' in [a if isinstance(a, str) else a.get('path') for a in test_attachments]:
        try:
            import os
            os.remove("sample.pdf")
            os.remove("sample.jpg")
        except OSError:
            pass
else:
    # Create dummy files if module is imported and SMTP_SERVERS are not set (e.g. for app.py)
    # This is to prevent FileNotFoundError if app.py tries to access them without sender.py being run directly.
    if not SMTP_SERVERS or 'YOUR_MAILTRAP_USERNAME' in SMTP_SERVERS[0].get('username', ''):
        try:
            with open("sample.pdf", "w") as f: f.write("This is a dummy PDF.")
            with open("sample.jpg", "w") as f: f.write("This is a dummy JPG.")
        except Exception:
            pass # Silently fail if cannot create dummy files

print("sender.py loaded.")
if not SMTP_SERVERS:
    print("Warning: sender.py:SMTP_SERVERS list is empty. Email sending will fail until configured.")
elif 'YOUR_MAILTRAP_USERNAME' in SMTP_SERVERS[0].get('username',''):
     print("Warning: sender.py:SMTP_SERVERS is using Mailtrap placeholder. Configure with real SMTP details for actual sending.")
