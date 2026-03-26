import smtplib
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from playwright.sync_api import sync_playwright

def convert_html_to_pdf(html_content, output_filename):
    """Converts HTML content to a PDF file using Playwright."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html_content)
            page.pdf(path=output_filename)
            browser.close()
        return True
    except Exception as e:
        print(f"Error converting HTML to PDF: {e}")
        return False

def convert_html_to_image(html_content, output_filename, img_format='png'):
    """Converts HTML content to an image file using Playwright."""
    try:
        # Playwright screenshot supports 'png' or 'jpeg'
        playwright_format = 'png' if img_format.lower() == 'png' else 'jpeg'
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html_content)
            page.screenshot(path=output_filename, type=playwright_format)
            browser.close()
        return True
    except Exception as e:
        print(f"Error converting HTML to Image: {e}")
        return False

def send_spoofed_email_with_attachments(config, attachments):
    """
    Sends an email appearing to originate from Box, with a custom sender name and attachments.
    """
    sender_name = config.get('sender_name')
    sender_email = config.get('sender_email')
    recipient_emails = config.get('recipient_emails', [])
    subject = config.get('subject')
    body = config.get('body')

    smtp_server = config.get('smtp_server')
    smtp_port = config.get('smtp_port', 587)
    smtp_user = config.get('smtp_user')
    smtp_pass = config.get('smtp_pass')

    try:
        print(f"Connecting to SMTP server {smtp_server}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)

        for recipient_email in recipient_emails:
            msg = MIMEMultipart()
            msg['From'] = f"{sender_name} <{sender_email}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Attach files
            for filename, filepath in attachments:
                try:
                    with open(filepath, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f"attachment; filename= {filename}")
                        msg.attach(part)
                except Exception as e:
                    print(f"Error attaching file {filename}: {e}")

            try:
                # Send the email
                server.sendmail(sender_email, recipient_email, msg.as_string())
                print(f"Email sent successfully to {recipient_email}!")
            except Exception as e:
                print(f"Error sending email to {recipient_email}: {e}")

        server.quit()
    except Exception as e:
        print(f"SMTP error: {e}")

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found. Please create it based on config.json.example.")
        exit(1)

    with open(config_path, 'r') as f:
        config = json.load(f)

    html_content = config.get('html_content', "<html><body><h1>Default Content</h1></body></html>")

    pdf_filename = "attachment.pdf"
    png_filename = "attachment.png"

    print("Converting HTML to PDF...")
    convert_html_to_pdf(html_content, pdf_filename)

    print("Converting HTML to Image...")
    convert_html_to_image(html_content, png_filename)

    attachments = [
        ("security_notice.pdf", pdf_filename),
        ("security_image.png", png_filename)
    ]

    # Only attempt to send if not in a dry run or similar (though not explicitly requested,
    # let's just follow the provided logic structure)
    # The user provided example called the function directly.

    send_spoofed_email_with_attachments(config, attachments)

    # Clean up temporary files
    if os.path.exists(pdf_filename):
        os.remove(pdf_filename)
    if os.path.exists(png_filename):
        os.remove(png_filename)
