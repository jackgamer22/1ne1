import smtplib
import imaplib
import json
import time
import os
import mimetypes
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()

BANNER = """
**********************************
*      MAGXXICVOT B2B SNDR       *
**********************************
"""

stats = []

def get_stats_table():
    table = Table(title="MAGXXICVOT B2B SNDR Dashboard")
    table.add_column("Time", style="cyan")
    table.add_column("Recipient", style="magenta")
    table.add_column("Subject", style="green")
    table.add_column("Status", style="bold yellow")

    for row in stats:
        table.add_row(*row)
    return table

def move_sent_email(config, recipient, subject):
    imap_cfg = config['imap']
    try:
        if imap_cfg.get('use_ssl'):
            mail = imaplib.IMAP4_SSL(imap_cfg['host'], imap_cfg['port'])
        else:
            mail = imaplib.IMAP4(imap_cfg['host'], imap_cfg['port'])

        mail.login(imap_cfg['user'], imap_cfg['password'])
        mail.select('Sent')

        search_criteria = f'(TO "{recipient}" SUBJECT "{subject}")'
        result, data = mail.search(None, search_criteria)

        status = "Sent mail not found"
        if result == 'OK' and data[0]:
            latest_email_id = data[0].split()[-1]
            archive_folder = imap_cfg.get('archive_folder', 'Archive')
            result = mail.copy(latest_email_id, archive_folder)

            if result[0] == 'OK':
                mail.store(latest_email_id, '+FLAGS', '\\Deleted')
                mail.expunge()
                status = f"Moved to {archive_folder}"
            else:
                status = "Move failed"

        mail.logout()
        return status
    except Exception as e:
        return f"IMAP Error: {e}"

def get_conversation_context(config, recipient):
    imap_cfg = config['imap']
    try:
        if imap_cfg.get('use_ssl'):
            mail = imaplib.IMAP4_SSL(imap_cfg['host'], imap_cfg['port'])
        else:
            mail = imaplib.IMAP4(imap_cfg['host'], imap_cfg['port'])

        mail.login(imap_cfg['user'], imap_cfg['password'])
        mail.select('INBOX')

        # Search for messages from the recipient
        result, data = mail.search(None, f'FROM "{recipient}"')
        context = "our collaboration" # Default context

        if result == 'OK' and data[0]:
            latest_id = data[0].split()[-1]
            result, msg_data = mail.fetch(latest_id, '(BODY[HEADER.FIELDS (SUBJECT)])')
            if result == 'OK':
                subject_header = msg_data[0][1].decode().strip()
                if subject_header.startswith("Subject:"):
                    context = subject_header[8:].strip()

        mail.logout()
        return context
    except Exception:
        return "our previous contact"

def send_email(config, recipient, context):
    smtp_cfg = config['smtp']
    email_cfg = config['email']

    subject = email_cfg['subject'].replace('{{ context }}', context)
    body_text = email_cfg['body'].replace('{{ context }}', context)

    msg = MIMEMultipart()
    msg['From'] = smtp_cfg['user']
    msg['To'] = recipient
    msg['Subject'] = subject

    use_html = email_cfg.get('use_html', True)

    if use_html:
        logo_html = ""
        if email_cfg.get('logo_base64'):
            logo_html = f'<img src="data:image/png;base64,{email_cfg["logo_base64"]}" alt="Logo"><br>'

        signature_html = f'<br>--<br>{email_cfg.get("signature", "")}'

        html_content = f"""
        <html>
          <body>
            {logo_html}
            <p>{body_text.replace('\n', '<br>')}</p>
            {signature_html}
          </body>
        </html>
        """
        msg.attach(MIMEText(html_content, 'html'))
    else:
        full_body = f"{body_text}\n\n--\n{email_cfg.get('signature', '')}"
        msg.attach(MIMEText(full_body, 'plain'))

    # Attachments
    for file_path in email_cfg.get('attachments', []):
        if os.path.exists(file_path):
            ctype, encoding = mimetypes.guess_type(file_path)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)

            try:
                with open(file_path, 'rb') as f:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
                    msg.attach(part)
            except Exception as e:
                console.print(f"[red]Error attaching {file_path}: {e}[/red]")

    try:
        server = smtplib.SMTP(smtp_cfg['host'], smtp_cfg['port'])
        if smtp_cfg.get('use_tls'):
            server.starttls()
        server.login(smtp_cfg['user'], smtp_cfg['password'])
        server.send_message(msg)
        server.quit()
        return True, subject
    except Exception as e:
        return False, str(e)

def run_automation():
    console.print(BANNER, style="bold blue")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        console.print("[bold red]config.json not found! 😱[/bold red]")
        return

    contacts = config['email'].get('contacts', [])

    with Live(get_stats_table(), refresh_per_second=4) as live:
        for recipient in contacts:
            current_time = datetime.now().strftime("%H:%M:%S")

            # 1. Fetch Context
            context = get_conversation_context(config, recipient)

            # 2. Send Email
            success, result_info = send_email(config, recipient, context)

            if success:
                subject = result_info
                status = "Sent. Waiting..."
                stats.append([current_time, recipient, subject, status])
                live.update(get_stats_table())

                time.sleep(5)

                # 3. Move Email
                move_status = move_sent_email(config, recipient, subject)
                stats[-1][3] = f"Sent & {move_status}"
            else:
                stats.append([current_time, recipient, "N/A", f"Failed: {result_info[:20]}"])

            live.update(get_stats_table())

    console.print("\n[bold green]✅ Automation cycle complete.[/bold green]")

if __name__ == "__main__":
    run_automation()
