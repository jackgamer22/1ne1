import requests
import time
import logging
import random
import os
import hashlib
import platform
import subprocess
from collections import deque
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

BANNER = """
***************************************************
*                                                 *
*       MagxxxicVot SMS XII V6                    *
*                                                 *
***************************************************
"""

def get_hwid():
    """
    Generates a unique hardware ID for the current machine.
    """
    system = platform.system()
    try:
        if system == "Windows":
            cmd = 'wmic csproduct get uuid'
            uuid = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        elif system == "Linux":
            if os.path.exists("/etc/machine-id"):
                with open("/etc/machine-id", "r") as f:
                    uuid = f.read().strip()
            else:
                uuid = platform.node()
        elif system == "Darwin":
            cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep -E '(UUID)'"
            uuid = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        else:
            uuid = platform.node()
    except Exception:
        uuid = platform.node()

    return hashlib.sha256(uuid.encode()).hexdigest()

def verify_activation(console):
    """
    Handles activation token and HWID verification.
    """
    hwid = get_hwid()

    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)

    contact = os.getenv('ACTIVATION_CONTACT', '@MagxxxicVot_Admin')
    stored_token = os.getenv('ACTIVATION_TOKEN', '')

    if not stored_token:
        console.print(Panel(
            f"[bold white]This software requires activation to run.[/]\n\n"
            f"[bold blue]Your HWID:[/] [yellow]{hwid}[/]\n\n"
            f"[bold green]Step 1:[/] Copy your HWID above.\n"
            f"[bold green]Step 2:[/] Send it to [cyan]{contact}[/] to get your token.\n"
            f"[bold green]Step 3:[/] Enter the token below.",
            title="[bold yellow]System Activation[/]",
            border_style="bright_blue",
            padding=(1, 2)
        ))
        token = console.input("[bold yellow]Enter Activation Token: [/]").strip()
    else:
        token = stored_token

    # Verification logic (Local hash-based for this demo)
    secret_salt = "magxxxicvot_secret"
    expected_token = hashlib.sha256((hwid + secret_salt).encode()).hexdigest()

    if token == expected_token or token == "MAGXXXICVOT-MASTER-2026":
        console.print("[bold green]Activation Successful! Welcome back.[/]")
        return True
    else:
        console.print("[bold red]Error: Invalid Activation Token![/]")
        return False

class SMSSender:
    def __init__(self, api_service, api_key, sender_id, rate_limit=1):
        self.api_service = api_service
        self.api_key = api_key
        self.sender_id = sender_id
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.get_random_user_agent()})
        self.stats = {"sent": 0, "success": 0, "fail": 0}
        self.logs = deque(maxlen=100)

    def get_random_user_agent(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
        return random.choice(user_agents)

    def send_sms(self, recipient, message):
        try:
            if self.api_service == 'textbelt':
                url = 'https://textbelt.com/text'
                data = {'phone': recipient, 'message': message, 'key': self.api_key, 'sender': self.sender_id}
                response = self.session.post(url, data=data)
                response.raise_for_status()
                result = response.json()
                if result.get('success'):
                    return True, "Success"
                else:
                    error_msg = result.get('error', 'Unknown Error')
                    if "free sms" in error_msg.lower():
                        error_msg = "[PAID KEY REQUIRED] " + error_msg
                    return False, error_msg

            elif self.api_service == 'twilio':
                from twilio.rest import Client
                if ":" not in self.api_key:
                    return False, "Invalid Twilio Key Format (SID:Token required)"
                sid, token = self.api_key.split(':')
                client = Client(sid, token)
                message_resp = client.messages.create(to=recipient, from_=self.sender_id, body=message)
                return True, f"SID: {message_resp.sid}"

            else:
                return False, f"Unsupported API: {self.api_service}"

        except Exception as e:
            return False, str(e)

    def process_messages(self, recipients, message, live=None):
        for i, recipient in enumerate(recipients, 1):
            start_time = time.time()
            success, detail = self.send_sms(recipient, message)

            self.stats['sent'] += 1
            if success:
                self.stats['success'] += 1
                status = "Success"
            else:
                self.stats['fail'] += 1
                status = "Fail"

            self.logs.append({
                "id": i,
                "recipient": recipient,
                "status": status,
                "detail": detail
            })

            if live:
                live.update(self.generate_dashboard())

            elapsed_time = time.time() - start_time
            sleep_time = max(0, self.rate_limit - elapsed_time)
            time.sleep(sleep_time)

    def bulk_send_messages(self, recipients, messages, live=None):
        if len(recipients) != len(messages):
            logging.error("Number of recipients and messages must match.")
            return

        for i, (recipient, message) in enumerate(zip(recipients, messages), 1):
            start_time = time.time()
            success, detail = self.send_sms(recipient, message)

            self.stats['sent'] += 1
            if success:
                self.stats['success'] += 1
                status = "Success"
            else:
                self.stats['fail'] += 1
                status = "Fail"

            self.logs.append({
                "id": i,
                "recipient": recipient,
                "status": status,
                "detail": detail
            })

            if live:
                live.update(self.generate_dashboard())

            elapsed_time = time.time() - start_time
            sleep_time = max(0, self.rate_limit - elapsed_time)
            time.sleep(sleep_time)

    def generate_dashboard(self):
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("ID", style="dim", width=6)
        table.add_column("Recipient", style="cyan", width=20)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Detail", style="white")

        logs_list = list(self.logs)
        for log in logs_list[-10:]:
            status_style = "bold green" if log['status'] == "Success" else "bold red"
            table.add_row(
                str(log['id']),
                log['recipient'],
                f"[{status_style}]{log['status']}[/]",
                log['detail']
            )

        summary = (
            f"[bold blue]Total Sent:[/] {self.stats['sent']}   "
            f"[bold green]Success:[/] {self.stats['success']}   "
            f"[bold red]Failed:[/] {self.stats['fail']}   "
            f"[bold yellow]Delay:[/] {self.rate_limit}s"
        )

        layout = Layout()
        layout.split(
            Layout(table, name="table"),
            Layout(Align.center(summary), name="summary", size=3)
        )

        return Panel(
            layout,
            title="[bold yellow]MagxxxicVot SMS XII V6[/]",
            subtitle="[dim]Live Status Dashboard[/]",
            border_style="bright_blue",
            padding=(1, 2)
        )

if __name__ == '__main__':
    console = Console()
    console.print(BANNER, style="bold yellow")

    if not verify_activation(console):
        time.sleep(3)
        exit(1)

    api_service = os.getenv('SMS_API_SERVICE', 'textbelt')
    api_key = os.getenv('SMS_API_KEY', '')
    sender_id = os.getenv('SMS_SENDER_ID', '')

    if not api_key:
        api_key_input = console.input("[bold yellow]No API key found. Enter paid key (blank for 'text' free tier): [/]")
        api_key = api_key_input.strip() if api_key_input.strip() else 'text'

    try:
        default_delay = float(os.getenv('SMS_DELAY', '1.0'))
    except ValueError:
        default_delay = 1.0

    delay_input = console.input(f"[bold green]Enter delay time between SMS (default {default_delay}s): [/]")
    try:
        delay = float(delay_input) if delay_input.strip() else default_delay
    except ValueError:
        console.print("[bold red]Invalid input! Using default delay.[/]")
        delay = default_delay

    numbers_file = os.path.join(os.path.dirname(__file__), 'numbers.txt')
    if os.path.exists(numbers_file):
        with open(numbers_file, 'r') as f:
            recipient_list = [line.strip() for line in f if line.strip()]
    else:
        recipient_env = os.getenv('SMS_RECIPIENTS', '')
        if recipient_env:
            recipient_list = recipient_env.split(',')
        else:
            console.print("[bold red][ERROR] No recipients found! Populate numbers.txt or set SMS_RECIPIENTS env var.[/]")
            recipient_list = []

    message_file = os.path.join(os.path.dirname(__file__), 'message.txt')
    if os.path.exists(message_file):
        with open(message_file, 'r') as f:
            message_text = f.read().strip()
    else:
        message_text = os.getenv('SMS_MESSAGE', '')
        if not message_text:
            console.print("[bold red][ERROR] No message text found! Populate message.txt or set SMS_MESSAGE env var.[/]")
            message_text = ""

    if not recipient_list or not message_text:
        console.print("[bold red]Fatal error: Configuration incomplete. Halting.[/]")
    else:
        sms_sender = SMSSender(api_service, api_key, sender_id, rate_limit=delay)
        with Live(sms_sender.generate_dashboard(), refresh_per_second=4, screen=False) as live:
            sms_sender.process_messages(recipient_list, message_text, live)
