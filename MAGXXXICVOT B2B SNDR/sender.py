import smtplib
import imaplib
import json
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BANNER = """
**********************************
*      MAGXXICVOT B2B SNDR       *
**********************************
"""

def move_sent_email(config, recipient):
    imap_cfg = config['imap']
    email_cfg = config['email']

    try:
        if imap_cfg.get('use_ssl'):
            mail = imaplib.IMAP4_SSL(imap_cfg['host'], imap_cfg['port'])
        else:
            mail = imaplib.IMAP4(imap_cfg['host'], imap_cfg['port'])

        mail.login(imap_cfg['user'], imap_cfg['password'])
        mail.select('Sent')

        # Search for the email we just sent
        search_criteria = f'(TO "{recipient}" SUBJECT "{email_cfg["subject"]}")'
        result, data = mail.search(None, search_criteria)

        if result == 'OK' and data[0]:
            latest_email_id = data[0].split()[-1]
            archive_folder = imap_cfg.get('archive_folder', 'Archive')
            result = mail.copy(latest_email_id, archive_folder)

            if result[0] == 'OK':
                mail.store(latest_email_id, '+FLAGS', '\\Deleted')
                mail.expunge()
                print(f"Email moved to {archive_folder} successfully.")
            else:
                print(f"Could not copy email to {archive_folder}.")
        else:
            print(f"Could not find sent email for {recipient} to move.")

        mail.logout()
        return True
    except Exception as e:
        print(f"IMAP error: {e}. Oh well, it's stuck in the Sent folder forever. 🤷‍♂️")
        return False

def send_email(config, recipient):
    smtp_cfg = config['smtp']
    email_cfg = config['email']

    msg = MIMEMultipart('related')
    msg['From'] = smtp_cfg['user']
    msg['To'] = recipient
    msg['Subject'] = email_cfg['subject']

    # HTML Body with Logo and Signature
    logo_html = ""
    if email_cfg.get('logo_base64'):
        logo_html = f'<img src="data:image/png;base64,{email_cfg["logo_base64"]}" alt="Logo"><br>'

    signature_html = f'<br>--<br>{email_cfg.get("signature", "")}'

    html_content = f"""
    <html>
      <body>
        {logo_html}
        <p>{email_cfg['body'].replace('\n', '<br>')}</p>
        {signature_html}
      </body>
    </html>
    """

    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(smtp_cfg['host'], smtp_cfg['port'])
        if smtp_cfg.get('use_tls'):
            server.starttls()
        server.login(smtp_cfg['user'], smtp_cfg['password'])
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"Oops! Something went wrong while sending to {recipient}: {e}. 🤡")
        return False

def run_automation():
    print(BANNER)
    print("🚀 Starting MAGXXXICVOT B2B SNDR automation...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Wait, where's config.json? I need it to work! 😱")
        return

    contacts = config['email'].get('contacts', [])
    if not contacts:
        # Fallback to single 'to' field if 'contacts' is missing
        single_to = config['email'].get('to')
        if single_to:
            contacts = [single_to]
        else:
            print("No recipients found in config! 😵")
            return

    for recipient in contacts:
        print(f"\nProcessing contact: {recipient}")
        if send_email(config, recipient):
            print("Waiting a few seconds for the email to appear in 'Sent' folder...")
            time.sleep(5)
            move_sent_email(config, recipient)

    print("\n✅ Automation cycle complete.")

if __name__ == "__main__":
    run_automation()
