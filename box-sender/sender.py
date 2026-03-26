import sys
import os

# Pre-startup dependency check
missing_deps = []
try:
    import playwright
except ImportError:
    missing_deps.append("playwright")
try:
    import rich
except ImportError:
    missing_deps.append("rich")
try:
    import minify_html
except ImportError:
    missing_deps.append("minify-html")
try:
    import dkim
except ImportError:
    missing_deps.append("dkimpy")

if missing_deps:
    print(f"Error: Missing required Python libraries: {', '.join(missing_deps)}")
    print("Please run setup.bat (on Windows) or: pip install -r requirements.txt")
    sys.exit(1)

import smtplib
import imaplib
import json
import time
import argparse
import getpass
import random
import string
import ssl
from email import policy
from email.utils import formatdate, make_msgid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box
from rich.panel import Panel
from rich.layout import Layout
from datetime import datetime

console = Console()

def minify_html_content(html_content):
    """Minifies the provided HTML content using minify-html."""
    try:
        return minify_html.minify(html_content, minify_js=True, minify_css=True)
    except Exception as e:
        console.print(f"[yellow]HTML minification failed: {e}. Using original HTML.[/yellow]")
        return html_content

def personalize_content(content, recipient_email, config):
    """Replaces personalization tags in the content."""
    replacements = {
        "[-email-]": recipient_email,
        "[-sender_name-]": config.get('sender_name', 'Box Security'),
        "[-sender_email-]": config.get('sender_email', 'security@box.com')
    }
    for tag, value in replacements.items():
        content = content.replace(tag, value)
    return content

def get_sent_folder(imap):
    """Detects the Sent folder name in an IMAP account."""
    try:
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
    except:
        return 'Sent'

def create_summary_panel(sent_count, fail_count, sync_count, total, use_imap):
    """Creates a summary panel showing overall status."""
    summary_text = (
        f"[bold cyan]Total Recipients:[/] {total}\n"
        f"[bold green]Sent Successfully:[/] {sent_count}\n"
        f"[bold red]Failed Emails:[/] {fail_count}\n"
    )
    if use_imap:
        summary_text += f"[bold magenta]IMAP Synced:[/] {sync_count}"
    else:
        summary_text += f"[italic grey]IMAP Sync: Disabled[/italic grey]"

    return Panel(summary_text, title="[bold white]Summary[/bold white]", box=box.ROUNDED, border_style="blue")

def create_status_table(status_data, use_imap):
    """Creates a beautiful rich table for the status dashboard."""
    table = Table(box=box.SIMPLE, header_style="bold blue", expand=True)
    table.add_column("Recipient", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    if use_imap:
        table.add_column("Sync", style="magenta")
    table.add_column("Time", justify="right")

    for entry in status_data[-10:]:
        status_color = "green" if entry['status'] == "Sent" else "yellow" if "..." in entry['status'] else "red"

        row = [
            entry['recipient'],
            f"[{status_color}]{entry['status']}[/{status_color}]"
        ]

        if use_imap:
            sync_color = "green" if entry['sync'] == "Synced" else "yellow" if entry['sync'] == "Skipped" else "red"
            row.append(f"[{sync_color}]{entry['sync']}[/{sync_color}]")

        row.append(entry['time'])
        table.add_row(*row)

    return Panel(table, title="[bold white]Real-time Log[/bold white]", box=box.ROUNDED, border_style="blue")

def create_dashboard_layout(status_data, sent_count, fail_count, sync_count, total, use_imap):
    """Assembles the advanced dashboard layout."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main")
    )
    layout["header"].update(Panel("[bold white]Box Sender - Advanced Dashboard[/bold white]", box=box.SQUARE, border_style="blue", style="on blue", subtitle="v2.7"))

    main_layout = Layout()
    main_layout.split_row(
        Layout(create_summary_panel(sent_count, fail_count, sync_count, total, use_imap), name="summary", size=30),
        Layout(create_status_table(status_data, use_imap), name="table")
    )
    layout["main"].update(main_layout)
    return layout

def load_leads(leads_path):
    """Loads email addresses from a leads text file."""
    if not leads_path or not os.path.exists(leads_path):
        return []
    try:
        with open(leads_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and '@' in line]
    except Exception as e:
        return []

def get_smtp_connection(server_host, port, user, password):
    """Establishes an SMTP connection supporting both Port 465 (SSL) and Port 587 (STARTTLS)."""
    context = ssl.create_default_context()
    if port == 465:
        server = smtplib.SMTP_SSL(server_host, port, context=context)
    else:
        server = smtplib.SMTP(server_host, port)
        server.starttls(context=context)
    server.login(user, password)
    return server

def sign_with_dkim(msg, config):
    """Signs the email message with DKIM if configured."""
    if not config.get('use_dkim', False):
        return msg

    selector = config.get('dkim_selector')
    domain = config.get('sender_email', '').split('@')[-1]
    key_path = config.get('dkim_private_key_path')

    if not all([selector, domain, key_path]) or not os.path.exists(key_path):
        console.print("[yellow]DKIM configuration incomplete or key file missing. Skipping signing.[/yellow]")
        return msg

    try:
        with open(key_path, 'rb') as f:
            private_key = f.read()

        headers_to_sign = [b'from', b'to', b'subject', b'date', b'message-id']
        sig = dkim.sign(msg.as_bytes(), selector.encode(), domain.encode(), private_key, include_headers=headers_to_sign)
        # Signature comes back with "DKIM-Signature: ..." prefix
        sig_str = sig.decode()
        msg['DKIM-Signature'] = sig_str[len("DKIM-Signature: "):]
        return msg
    except Exception as e:
        console.print(f"[red]DKIM signing failed: {e}[/red]")
        return msg

def send_spoofed_email_with_attachments(config):
    """
    Sends an email appearing to originate from Box, with smart headers and optional attachments.
    Reuses browser and connections for maximum performance.
    """
    sender_name = config.get('sender_name')
    sender_email = config.get('sender_email')
    recipient_emails = config.get('recipient_emails', [])
    total = len(recipient_emails)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    letter_path = config.get('letter_path')
    if letter_path and os.path.exists(letter_path):
        with open(letter_path, 'r', encoding='utf-8') as f:
            letter_html_raw = f.read()
    else:
        letter_html_raw = config.get('body', "Default body content")

    attachment_html_raw = ""
    if config.get('send_attachments', True):
        attachment_html_path = config.get('attachment_html_path')
        if attachment_html_path and os.path.exists(attachment_html_path):
            with open(attachment_html_path, 'r', encoding='utf-8') as f:
                attachment_html_raw = f.read()
        else:
            attachment_html_raw = "<html><body><h1>Default Attachment Content</h1></body></html>"

    smtp_server = config.get('smtp_server')
    smtp_port = int(config.get('smtp_port', 587))
    smtp_user = config.get('smtp_user')
    smtp_pass = config.get('smtp_pass')

    use_imap = config.get('use_imap', False)
    imap_server = config.get('imap_server')
    imap_port = int(config.get('imap_port', 993))
    imap_user = config.get('imap_user')
    imap_pass = config.get('imap_pass')

    delay = config.get('delay_seconds', 0)

    status_data = []
    sent_count = 0
    fail_count = 0
    sync_count = 0

    with Live(create_dashboard_layout(status_data, sent_count, fail_count, sync_count, total, use_imap), refresh_per_second=4) as live, sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            console.print(f"Connecting to SMTP server {smtp_server}...")
            server = get_smtp_connection(smtp_server, smtp_port, smtp_user, smtp_pass)

            imap = None
            sent_folder = None
            if use_imap and all([imap_server, imap_user, imap_pass]):
                try:
                    console.print(f"Connecting to IMAP server {imap_server}...")
                    imap = imaplib.IMAP4_SSL(imap_server, imap_port)
                    imap.login(imap_user, imap_pass)
                    sent_folder = get_sent_folder(imap)
                except Exception as e:
                    console.print(f"[yellow]IMAP login error: {e}. Skipping Sent folder sync.[/yellow]")
                    imap = None

            for i, recipient_email in enumerate(recipient_emails):
                if i > 0 and delay > 0:
                    time.sleep(delay)

                entry = {'recipient': recipient_email, 'status': 'Processing...', 'sync': 'Pending', 'time': datetime.now().strftime("%H:%M:%S")}
                status_data.append(entry)
                live.update(create_dashboard_layout(status_data, sent_count, fail_count, sync_count, total, use_imap))

                msg = MIMEMultipart(policy=policy.default)
                msg['From'] = f"{sender_name} <{sender_email}>"
                msg['To'] = recipient_email
                msg['Subject'] = personalize_content(config.get('subject', ''), recipient_email, config)

                msg['Date'] = formatdate(localtime=True)
                msg['Message-ID'] = make_msgid(domain=sender_email.split('@')[-1])
                msg['X-Mailer'] = "MagxxicVox/2.7 (Box Security Tool)"
                msg['X-Priority'] = '1 (Highest)'
                msg['X-MSMail-Priority'] = 'High'
                msg['Importance'] = 'High'

                personalized_body = personalize_content(letter_html_raw, recipient_email, config)
                msg.attach(MIMEText(minify_html_content(personalized_body), 'html'))

                if config.get('send_attachments', True) and attachment_html_raw:
                    personalized_attach_html = personalize_content(attachment_html_raw, recipient_email, config)
                    minified_attach_html = minify_html_content(personalized_attach_html)

                    fmt = config.get('attachment_format', 'pdf').lower()
                    extension = 'png' if fmt in ['img', 'png'] else 'pdf' if fmt == 'pdf' else 'svg'
                    filename = f"security_notice_{i}.{extension}"
                    filepath = os.path.join(script_dir, filename)

                    page.set_content(minified_attach_html)
                    if extension == 'pdf':
                        page.pdf(path=filepath)
                    else:
                        page.screenshot(path=filepath, type='png', full_page=True)

                    try:
                        with open(filepath, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f"attachment; filename= {filename}")
                            msg.attach(part)
                        os.remove(filepath)
                    except Exception as e:
                        console.print(f"[red]Error attaching file: {e}[/red]")

                # Apply DKIM signature
                msg = sign_with_dkim(msg, config)

                try:
                    entry['status'] = 'Sending...'
                    live.update(create_dashboard_layout(status_data, sent_count, fail_count, sync_count, total, use_imap))
                    msg_bytes = msg.as_bytes()
                    server.sendmail(smtp_user, recipient_email, msg_bytes)
                    entry['status'] = 'Sent'
                    sent_count += 1

                    if use_imap and imap and sent_folder:
                        imap.append(sent_folder, None, None, msg_bytes)
                        entry['sync'] = 'Synced'
                        sync_count += 1
                    else:
                        entry['sync'] = 'Skipped'
                except Exception as e:
                    entry['status'] = f'Failed: {e}'
                    entry['sync'] = 'Error'
                    fail_count += 1

                live.update(create_dashboard_layout(status_data, sent_count, fail_count, sync_count, total, use_imap))

            server.quit()
            if imap:
                imap.logout()
            browser.close()
        except Exception as e:
            console.print(f"[bold red]Critical Error: {e}[/bold red]")

def run_setup(config_path):
    """Interactive setup to configure SMTP/IMAP settings."""
    console.print("[bold blue]--- Box Sender Setup Wizard ---[/bold blue]")
    config = {}
    config['smtp_server'] = console.input("SMTP Server: ")
    config['smtp_port'] = int(console.input("SMTP Port (465/587): ") or 587)
    config['smtp_user'] = console.input("SMTP User: ")
    config['smtp_pass'] = getpass.getpass("SMTP Password: ")

    config['use_imap'] = console.input("Enable IMAP Sent folder sync? (y/n): ").lower() == 'y'
    if config['use_imap']:
        config['imap_server'] = console.input("IMAP Server: ")
        config['imap_port'] = int(console.input("IMAP Port (993): ") or 993)
        config['imap_user'] = console.input("IMAP User: ") or config['smtp_user']
        config['imap_pass'] = getpass.getpass("IMAP Password: ") or config['smtp_pass']

    config['use_dkim'] = console.input("Enable DKIM signing? (y/n): ").lower() == 'y'
    if config['use_dkim']:
        config['dkim_selector'] = console.input("DKIM Selector (e.g. default): ")
        config['dkim_private_key_path'] = console.input("Path to DKIM Private Key file: ")

    config['sender_name'] = console.input("Sender Display Name: ") or "Box Security"
    config['sender_email'] = console.input("Sender Email: ") or "security@box.com"
    config['leads_path'] = console.input("Path to leads file: ") or "leads/leads.txt"
    config['subject'] = console.input("Email Subject: ") or "Urgent Security Alert for [-email-]"
    config['letter_path'] = console.input("Path to letter.html: ") or "letter.html"
    config['attachment_html_path'] = console.input("Path to attachment.html: ") or "attachment.html"

    config['send_attachments'] = console.input("Send attachments? (y/n): ").lower() != 'n'
    if config['send_attachments']:
        config['attachment_format'] = console.input("Format (pdf, png): ").lower() or "pdf"

    config['delay_seconds'] = int(console.input("Delay in seconds (default 5): ") or 5)

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    console.print(f"[green]Configuration saved to {config_path}[/green]")
    return config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Box Sender Tool")
    parser.add_argument('--setup', action='store_true', help="Run setup wizard")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    if args.setup or not os.path.exists(config_path):
        config = run_setup(config_path)
    else:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

    if config.get('leads_path'):
        l_path = config['leads_path']
        if not os.path.isabs(l_path):
            l_path = os.path.join(script_dir, l_path)
        config['recipient_emails'] = load_leads(l_path)

    for key in ['letter_path', 'attachment_html_path', 'dkim_private_key_path']:
        if config.get(key) and not os.path.isabs(config[key]):
            config[key] = os.path.join(script_dir, config[key])

    send_spoofed_email_with_attachments(config)
