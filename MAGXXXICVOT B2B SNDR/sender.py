import smtplib
import imaplib
import json
import time
import argparse
import os
import mimetypes
import re
import socks
import socket
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import parseaddr
from urllib.parse import urlparse
from defusedxml import ElementTree as ET

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

class ProxyManager:
    def __init__(self, proxies):
        self.proxies = proxies
        self.valid_proxies = []
        self.current_index = 0

    def validate_proxies(self):
        console.print("🔍 Validating proxies...", style="cyan")
        for proxy_url in self.proxies:
            try:
                parsed = urlparse(proxy_url)
                proxy_type = socks.SOCKS5 if parsed.scheme == 'socks5' else socks.SOCKS4

                socks.set_default_proxy(
                    proxy_type,
                    parsed.hostname,
                    parsed.port,
                    username=parsed.username,
                    password=parsed.password
                )
                socket.socket = socks.socksocket

                response = requests.get('https://api.ipify.org', timeout=10)
                if response.status_code == 200:
                    console.print(f"✅ Proxy {proxy_url} is valid. IP: {response.text}", style="green")
                    self.valid_proxies.append(proxy_url)

                socks.set_default_proxy()
                socket.socket = socket._socket.socket if hasattr(socket, '_socket') else socket.socket
            except Exception as e:
                console.print(f"❌ Proxy {proxy_url} failed validation: {e}", style="red")

        return len(self.valid_proxies) > 0

    def get_next_proxy(self):
        if not self.valid_proxies:
            return None
        proxy = self.valid_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.valid_proxies)
        return proxy

    def apply_proxy(self, proxy_url):
        if not proxy_url:
            socks.set_default_proxy()
            return
        parsed = urlparse(proxy_url)
        proxy_type = socks.SOCKS5 if parsed.scheme == 'socks5' else socks.SOCKS4
        socks.set_default_proxy(
            proxy_type,
            parsed.hostname,
            parsed.port,
            username=parsed.username,
            password=parsed.password
        )
        socket.socket = socks.socksocket

def discover_server_settings(email):
    domain = email.split('@')[-1]
    url = f"https://autoconfig.thunderbird.net/v1.1/{domain}"

    console.print(f"🔍 Attempting auto-discovery for {domain}...", style="cyan")

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)

            imap_settings = {}
            smtp_settings = {}

            for server in root.findall('.//incomingServer'):
                if server.get('type') == 'imap':
                    imap_settings['host'] = server.find('hostname').text
                    imap_settings['port'] = int(server.find('port').text)
                    imap_settings['use_ssl'] = server.find('socketType').text == 'SSL'
                    break

            for server in root.findall('.//outgoingServer'):
                if server.get('type') == 'smtp':
                    smtp_settings['host'] = server.find('hostname').text
                    smtp_settings['port'] = int(server.find('port').text)
                    smtp_settings['use_tls'] = server.find('socketType').text == 'STARTTLS'
                    break

            if imap_settings and smtp_settings:
                console.print(f"✅ Auto-discovery successful for {domain}!", style="green")
                return imap_settings, smtp_settings
    except Exception as e:
        console.print(f"⚠️ Auto-discovery failed: {e}", style="yellow")

    # Fallback to common patterns
    console.print(f"⚠️ Falling back to common patterns for {domain}...", style="yellow")
    return {
        "host": f"imap.{domain}",
        "port": 993,
        "use_ssl": True
    }, {
        "host": f"smtp.{domain}",
        "port": 587,
        "use_tls": True
    }

def get_stats_table():
    table = Table(title="MAGXXICVOT B2B SNDR Dashboard")
    table.add_column("Time", style="cyan")
    table.add_column("Recipient", style="magenta")
    table.add_column("Subject", style="green")
    table.add_column("Status", style="bold yellow")

    for row in stats:
        table.add_row(*row)
    return table

def get_all_contacts(config, proxy_manager=None):
    imap_cfg = config['imap']
    contacts = set()

    if proxy_manager and config.get('proxy', {}).get('use_proxy'):
        proxy_manager.apply_proxy(proxy_manager.get_next_proxy())

    try:
        if imap_cfg.get('use_ssl'):
            mail = imaplib.IMAP4_SSL(imap_cfg['host'], imap_cfg['port'])
        else:
            mail = imaplib.IMAP4(imap_cfg['host'], imap_cfg['port'])

        mail.login(imap_cfg['user'], imap_cfg['password'])
        mail.select('INBOX')

        result, data = mail.search(None, 'ALL')
        if result == 'OK':
            ids = data[0].split()
            for msg_id in ids[-50:]:
                result, msg_data = mail.fetch(msg_id, '(BODY[HEADER.FIELDS (FROM)])')
                if result == 'OK':
                    from_header = msg_data[0][1].decode().strip()
                    name, addr = parseaddr(from_header.replace('From:', '').strip())
                    if addr and addr != imap_cfg['user']:
                        contacts.add(addr)

        mail.logout()
    except Exception as e:
        console.print(f"[red]Error discovering contacts: {e}[/red]")
    finally:
        socks.set_default_proxy()
    return list(contacts)

def move_sent_email(config, recipient, subject, proxy_manager=None):
    imap_cfg = config['imap']

    if proxy_manager and config.get('proxy', {}).get('use_proxy'):
        proxy_manager.apply_proxy(proxy_manager.get_next_proxy())

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
    finally:
        socks.set_default_proxy()

def get_conversation_context(config, recipient, proxy_manager=None):
    imap_cfg = config['imap']

    if proxy_manager and config.get('proxy', {}).get('use_proxy'):
        proxy_manager.apply_proxy(proxy_manager.get_next_proxy())

    try:
        if imap_cfg.get('use_ssl'):
            mail = imaplib.IMAP4_SSL(imap_cfg['host'], imap_cfg['port'])
        else:
            mail = imaplib.IMAP4(imap_cfg['host'], imap_cfg['port'])

        mail.login(imap_cfg['user'], imap_cfg['password'])
        mail.select('INBOX')

        result, data = mail.search(None, f'FROM "{recipient}"')
        context = "our collaboration"

        if result == 'OK' and data[0]:
            latest_id = data[0].split()[-1]
            result, msg_data = mail.fetch(latest_id, '(BODY[HEADER.FIELDS (SUBJECT)])')
            if result == 'OK':
                subject_header = msg_data[0][1].decode().strip()
                if subject_header.startswith("Subject:"):
                    context = subject_header[8:].strip()
                    context = re.sub(r'^(Re|Fwd|Aw|Wg):\s*', '', context, flags=re.IGNORECASE)

        mail.logout()
        return context
    except Exception:
        return "our previous contact"
    finally:
        socks.set_default_proxy()

def send_email(config, recipient, context, proxy_manager=None):
    smtp_cfg = config['smtp']
    email_cfg = config['email']

    if proxy_manager and config.get('proxy', {}).get('use_proxy'):
        proxy_manager.apply_proxy(proxy_manager.get_next_proxy())

    subject = email_cfg['subject'].replace('{{ context }}', context)

    if email_cfg.get('auto_draft_invite'):
        body_text = email_cfg.get('invite_template', '').replace('{{ context }}', context)
    else:
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
    finally:
        socks.set_default_proxy()

def run_automation():
    parser = argparse.ArgumentParser(description="MAGXXICVOT B2B SNDR Automation")
    parser.add_argument('--use-proxy', action='store_true', help='Force enable proxy usage')
    parser.add_argument('--no-proxy', action='store_true', help='Force disable proxy usage')
    args = parser.parse_args()

    console.print(BANNER, style="bold blue")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        console.print("[bold red]config.json not found! 😱[/bold red]")
        return

    # Auto-discovery
    auth_cfg = config.get('auth', {})
    if auth_cfg.get('auto_discovery'):
        email = auth_cfg.get('email')
        password = auth_cfg.get('password')
        if email and password and (not config.get('smtp') or not config.get('imap')):
            imap_discovered, smtp_discovered = discover_server_settings(email)

            if not config.get('imap'):
                config['imap'] = imap_discovered
                config['imap']['user'] = email
                config['imap']['password'] = password

            if not config.get('smtp'):
                config['smtp'] = smtp_discovered
                config['smtp']['user'] = email
                config['smtp']['password'] = password

    # Override config with CLI arguments
    if args.use_proxy:
        if 'proxy' not in config:
            config['proxy'] = {}
        config['proxy']['use_proxy'] = True
        console.print("[cyan]ℹ️ Proxy usage forced via CLI flag.[/cyan]")
    elif args.no_proxy:
        if 'proxy' not in config:
            config['proxy'] = {}
        config['proxy']['use_proxy'] = False
        console.print("[cyan]ℹ️ Proxy usage disabled via CLI flag.[/cyan]")

    # Proxy Setup
    proxy_manager = None
    if config.get('proxy', {}).get('use_proxy'):
        proxy_manager = ProxyManager(config['proxy'].get('proxies', []))
        if not proxy_manager.validate_proxies():
            console.print("[bold red]No valid proxies found. Exiting. 😱[/bold red]")
            return

    email_cfg = config['email']
    contacts = email_cfg.get('contacts', [])

    if email_cfg.get('auto_discover_contacts'):
        console.print("🔍 Discovering contacts from INBOX...")
        discovered = get_all_contacts(config, proxy_manager)
        contacts = list(set(contacts) | set(discovered))
        console.print(f"✅ Found {len(discovered)} new contacts.")

    if not contacts:
        console.print("[bold yellow]No contacts found to process.[/bold yellow]")
        return

    with Live(get_stats_table(), refresh_per_second=4) as live:
        for recipient in contacts:
            current_time = datetime.now().strftime("%H:%M:%S")
            context = get_conversation_context(config, recipient, proxy_manager)
            success, result_info = send_email(config, recipient, context, proxy_manager)

            if success:
                subject = result_info
                status = "Sent. Waiting..."
                stats.append([current_time, recipient, subject, status])
                live.update(get_stats_table())
                time.sleep(5)
                move_status = move_sent_email(config, recipient, subject, proxy_manager)
                stats[-1][3] = f"Sent & {move_status}"
            else:
                stats.append([current_time, recipient, "N/A", f"Failed: {result_info[:20]}"])

            live.update(get_stats_table())

    console.print("\n[bold green]✅ Automation cycle complete.[/bold green]")

if __name__ == "__main__":
    run_automation()
