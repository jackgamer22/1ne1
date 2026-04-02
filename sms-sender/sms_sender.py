import requests
import time
import logging
import random
import os
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

class SMSSender:
    def __init__(self, api_service, api_key, sender_id, rate_limit=1):
        self.api_service = api_service
        self.api_key = api_key
        self.sender_id = sender_id
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.get_random_user_agent()})
        self.stats = {"sent": 0, "success": 0, "fail": 0}
        self.logs = []

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

        for log in self.logs[-10:]:
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

    api_service = os.getenv('SMS_API_SERVICE', 'textbelt')
    api_key = os.getenv('SMS_API_KEY', '')
    sender_id = os.getenv('SMS_SENDER_ID', '')

    if not api_key:
        api_key_input = console.input("[bold yellow]Enter your API KEY (leave blank for 'textbelt' free tier): [/]")
        api_key = api_key_input.strip() if api_key_input.strip() else 'textbelt'

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
        recipient_list = os.getenv('SMS_RECIPIENTS', '').split(',')

    message_file = os.path.join(os.path.dirname(__file__), 'message.txt')
    if os.path.exists(message_file):
        with open(message_file, 'r') as f:
            message_text = f.read().strip()
    else:
        message_text = os.getenv('SMS_MESSAGE', 'Hello from MagxxxicVot SMS XII V6!')

    if not recipient_list or not recipient_list[0]:
        console.print("[bold red]No recipients configured![/]")
    else:
        sms_sender = SMSSender(api_service, api_key, sender_id, rate_limit=delay)
        with Live(sms_sender.generate_dashboard(), refresh_per_second=4, screen=False) as live:
            sms_sender.process_messages(recipient_list, message_text, live)
