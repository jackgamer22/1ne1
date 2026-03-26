import smtplib
import imaplib
import os
import json
import time
import argparse
import getpass
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

def get_sent_folder(imap):
    """Detects the Sent folder name in an IMAP account."""
    res, folders = imap.list()
    sent_folder = 'Sent'
    for folder in folders:
        folder_str = folder.decode()
        if 'sent' in folder_str.lower():
            parts = folder_str.split(' "/" ')
            if len(parts) > 1:
                sent_folder = parts[-1].strip('"')
            break
    return sent_folder

def send_spoofed_email_with_attachments(config, attachments):
    """
    Sends an email appearing to originate from Box, with a custom sender name and attachments.
    """
    sender_name = config.get('sender_name')
    sender_email = config.get('sender_email')
    recipient_emails = config.get('recipient_emails', [])
    subject = config.get('subject')

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

    imap_server = config.get('imap_server')
    imap_port = config.get('imap_port', 993)
    imap_user = config.get('imap_user')
    imap_pass = config.get('imap_pass')

    delay = config.get('delay_seconds', 0)

    try:
        print(f"Connecting to SMTP server {smtp_server}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)

        # Optional: Setup IMAP connection once for efficiency
        imap = None
        sent_folder = None
        if all([imap_server, imap_user, imap_pass]):
            try:
                print(f"Connecting to IMAP server {imap_server}...")
                imap = imaplib.IMAP4_SSL(imap_server, imap_port)
                imap.login(imap_user, imap_pass)
                sent_folder = get_sent_folder(imap)
            except Exception as e:
                print(f"IMAP login error: {e}. Skipping Sent folder sync.")
                imap = None

        for i, recipient_email in enumerate(recipient_emails):
            if i > 0 and delay > 0:
                print(f"Waiting {delay} seconds before sending next email...")
                time.sleep(delay)

            msg = MIMEMultipart(policy=policy.default)
            msg['From'] = f"{sender_name} <{sender_email}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body_html, 'html'))

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
                msg_bytes = msg.as_bytes()
                server.sendmail(sender_email, recipient_email, msg_bytes)
                print(f"Email sent successfully to {recipient_email}!")

                # Sync to IMAP Sent folder if available
                if imap and sent_folder:
                    imap.append(sent_folder, None, None, msg_bytes)
                    print(f"Email synced to IMAP folder: {sent_folder}")
            except Exception as e:
                print(f"Error sending email to {recipient_email}: {e}")

        server.quit()
        if imap:
            imap.logout()
    except Exception as e:
        print(f"SMTP error: {e}")

def run_setup(config_path):
    """Interactive setup to configure SMTP/IMAP settings."""
    print("--- Box Sender Setup Wizard ---")
    config = {}
    config['smtp_server'] = input("SMTP Server: ")
    config['smtp_port'] = int(input("SMTP Port (default 587): ") or 587)
    config['smtp_user'] = input("SMTP User: ")
    config['smtp_pass'] = getpass.getpass("SMTP Password: ")

    config['imap_server'] = input("IMAP Server: ")
    config['imap_port'] = int(input("IMAP Port (default 993): ") or 993)
    config['imap_user'] = input("IMAP User (often same as SMTP): ") or config['smtp_user']
    config['imap_pass'] = getpass.getpass("IMAP Password (often same as SMTP): ") or config['smtp_pass']

    config['sender_name'] = input("Sender Display Name (e.g. Box Security): ") or "Box Security"
    config['sender_email'] = input("Sender Email (e.g. security@box.com): ") or "security@box.com"
    config['recipient_emails'] = input("Recipient Emails (comma-separated): ").split(',')
    config['recipient_emails'] = [email.strip() for email in config['recipient_emails'] if email.strip()]

    config['subject'] = input("Email Subject: ") or "Urgent Security Alert: Verify Your Account"
    config['letter_path'] = input("Path to letter.html (default: letter.html): ") or "letter.html"
    config['attachment_html_path'] = input("Path to attachment.html (default: attachment.html): ") or "attachment.html"
    config['delay_seconds'] = int(input("Delay between emails in seconds (default: 5): ") or 5)

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {config_path}")
    return config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Box Sender Tool")
    parser.add_argument('--setup', action='store_true', help="Run the interactive setup wizard")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    if args.setup or not os.path.exists(config_path):
        config = run_setup(config_path)
    else:
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

    if os.path.exists(pdf_filename):
        os.remove(pdf_filename)
    if os.path.exists(png_filename):
        os.remove(png_filename)
