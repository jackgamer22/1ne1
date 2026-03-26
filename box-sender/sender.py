import smtplib
import imaplib
import os
import json
import time
from email import policy
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

def sync_to_sent_folder(config, msg_bytes):
    """Appends the sent email to the IMAP 'Sent' folder."""
    imap_server = config.get('imap_server')
    imap_port = config.get('imap_port', 993)
    imap_user = config.get('imap_user')
    imap_pass = config.get('imap_pass')

    if not all([imap_server, imap_user, imap_pass]):
        print("IMAP configuration incomplete. Skipping Sent folder sync.")
        return

    try:
        print(f"Connecting to IMAP server {imap_server}...")
        imap = imaplib.IMAP4_SSL(imap_server, imap_port)
        imap.login(imap_user, imap_pass)

        # Determine the name of the Sent folder (often 'Sent' or 'Sent Messages')
        res, folders = imap.list()
        sent_folder = 'Sent'
        for folder in folders:
            folder_str = folder.decode()
            if 'sent' in folder_str.lower():
                # Extract folder name from the list response
                # Example: (\HasNoChildren \Sent) "/" "Sent"
                parts = folder_str.split(' "/" ')
                if len(parts) > 1:
                    sent_folder = parts[-1].strip('"')
                break

        imap.append(sent_folder, None, None, msg_bytes)
        print(f"Email synced to IMAP folder: {sent_folder}")
        imap.logout()
    except Exception as e:
        print(f"Error syncing to IMAP Sent folder: {e}")

def send_spoofed_email_with_attachments(config, attachments):
    """
    Sends an email appearing to originate from Box, with a custom sender name and attachments.
    """
    sender_name = config.get('sender_name')
    sender_email = config.get('sender_email')
    recipient_emails = config.get('recipient_emails', [])
    subject = config.get('subject')

    # Load body from external file if possible
    letter_path = config.get('letter_path')
    if letter_path and os.path.exists(letter_path):
        with open(letter_path, 'r', encoding='utf-8') as f:
            body_html = f.read()
    else:
        body_html = config.get('body', "Default body content")

    smtp_server = config.get('smtp_server')
    smtp_port = config.get('smtp_port', 587)
    smtp_user = config.get('smtp_user')
    smtp_pass = config.get('smtp_pass')
    delay = config.get('delay_seconds', 0)

    try:
        print(f"Connecting to SMTP server {smtp_server}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)

        for i, recipient_email in enumerate(recipient_emails):
            if i > 0 and delay > 0:
                print(f"Waiting {delay} seconds before sending next email...")
                time.sleep(delay)

            msg = MIMEMultipart(policy=policy.default)
            msg['From'] = f"{sender_name} <{sender_email}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Email body as HTML
            msg.attach(MIMEText(body_html, 'html'))

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
                msg_bytes = msg.as_bytes()
                server.sendmail(sender_email, recipient_email, msg_bytes)
                print(f"Email sent successfully to {recipient_email}!")

                # Sync to IMAP
                sync_to_sent_folder(config, msg_bytes)
            except Exception as e:
                print(f"Error sending email to {recipient_email}: {e}")

        server.quit()
    except Exception as e:
        print(f"SMTP error: {e}")

if __name__ == "__main__":
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found. Please create it based on config.json.example.")
        exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Resolve relative paths in config based on the script directory
    for key in ['letter_path', 'attachment_html_path']:
        if config.get(key) and not os.path.isabs(config[key]):
            config[key] = os.path.join(script_dir, config[key])

    attachment_html_path = config.get('attachment_html_path')
    if attachment_html_path and os.path.exists(attachment_html_path):
        with open(attachment_html_path, 'r', encoding='utf-8') as f:
            attachment_html = f.read()
    else:
        attachment_html = "<html><body><h1>Default Attachment Content</h1></body></html>"

    pdf_filename = os.path.join(script_dir, "attachment.pdf")
    png_filename = os.path.join(script_dir, "attachment.png")

    print("Converting HTML to PDF...")
    convert_html_to_pdf(attachment_html, pdf_filename)

    print("Converting HTML to Image...")
    convert_html_to_image(attachment_html, png_filename)

    attachments = [
        ("security_notice.pdf", pdf_filename),
        ("security_image.png", png_filename)
    ]

    send_spoofed_email_with_attachments(config, attachments)

    # Clean up temporary files
    if os.path.exists(pdf_filename):
        os.remove(pdf_filename)
    if os.path.exists(png_filename):
        os.remove(png_filename)
