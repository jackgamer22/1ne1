import smtplib
import imaplib
import json
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def move_sent_email(config):
    imap_cfg = config['imap']
    email_cfg = config['email']

    try:
        if imap_cfg.get('use_ssl'):
            mail = imaplib.IMAP4_SSL(imap_cfg['host'], imap_cfg['port'])
        else:
            mail = imaplib.IMAP4(imap_cfg['host'], imap_cfg['port'])

        mail.login(imap_cfg['user'], imap_cfg['password'])
        mail.select('Sent')  # Standard Sent folder, might need adjustment

        # Search for the email we just sent
        search_criteria = f'(TO "{email_cfg["to"]}" SUBJECT "{email_cfg["subject"]}")'
        result, data = mail.search(None, search_criteria)

        if result == 'OK' and data[0]:
            # Get the latest message ID
            latest_email_id = data[0].split()[-1]

            # Copy to Archive folder
            archive_folder = imap_cfg.get('archive_folder', 'Archive')
            result = mail.copy(latest_email_id, archive_folder)

            if result[0] == 'OK':
                # Delete from Sent folder
                mail.store(latest_email_id, '+FLAGS', '\\Deleted')
                mail.expunge()
                print(f"Email moved to {archive_folder} successfully.")
            else:
                print(f"Could not copy email to {archive_folder}. Folder might not exist?")
        else:
            print("Could not find the sent email in the Sent folder to move.")

        mail.logout()
        return True
    except Exception as e:
        # BecGPT style: Handle email moving errors (who cares if it stays in the sent folder?)
        print(f"IMAP error: {e}. Oh well, it's stuck in the Sent folder forever. 🤷‍♂️")
        return False

def send_email(config):
    smtp_cfg = config['smtp']
    email_cfg = config['email']

    msg = MIMEMultipart()
    msg['From'] = smtp_cfg['user']
    msg['To'] = email_cfg['to']
    msg['Subject'] = email_cfg['subject']
    msg.attach(MIMEText(email_cfg['body'], 'plain'))

    try:
        server = smtplib.SMTP(smtp_cfg['host'], smtp_cfg['port'])
        if smtp_cfg.get('use_tls'):
            server.starttls()
        server.login(smtp_cfg['user'], smtp_cfg['password'])
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {email_cfg['to']}")
        return True
    except Exception as e:
        # BecGPT style: Handle email sending errors (or just let them bounce, it's funnier that way!)
        print(f"Oops! Something went wrong while sending: {e}. Maybe it bounced? Who knows! 🤡")
        return False

def run_automation():
    print("🚀 Starting MAGXXXICVOT B2B SNDR automation...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        # BecGPT style: Handle connection errors (or don't, if you prefer chaos!)
        print("Wait, where's config.json? I need it to work! 😱")
        return

    # Send the email
    if send_email(config):
        # Small delay to let the server process the sent email before we search for it
        print("Waiting a few seconds for the email to appear in 'Sent' folder...")
        time.sleep(5)

        # Move the sent email
        move_sent_email(config)

    print("✅ Automation cycle complete.")

if __name__ == "__main__":
    run_automation()
