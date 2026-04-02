import requests
import time
import logging
import random
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BANNER = """
***************************************************
*                                                 *
*       MagxxxicVot SMS XII V6                    *
*                                                 *
***************************************************
"""

class SMSSender:
    def __init__(self, api_service, api_key, sender_id, rate_limit=1):
        """
        Initializes the SMS Sender with API details.

        Args:
            api_service (str): 'textbelt', 'twilio', 'aws', 'telesign'
            api_key (str): The API key for the service.
            sender_id (str): The sender ID (phone number or alphanumeric).
            rate_limit (float): Delay in seconds between messages to respect rate limits.
        """
        self.api_service = api_service
        self.api_key = api_key
        self.sender_id = sender_id
        self.rate_limit = rate_limit
        self.session = requests.Session()

        # Add a custom user agent
        self.session.headers.update({'User-Agent': self.get_random_user_agent()})

    def get_random_user_agent(self):
        """
        Returns a random User-Agent string.
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
        return random.choice(user_agents)

    def send_sms(self, recipient, message):
        """
        Sends an SMS message via the specified API service.

        Args:
            recipient (str): The recipient's phone number.
            message (str): The message to send.

        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        try:
            if self.api_service == 'textbelt':
                url = 'https://textbelt.com/text'
                data = {
                    'phone': recipient,
                    'message': message,
                    'key': self.api_key,
                    'sender': self.sender_id
                }
                response = self.session.post(url, data=data)
                response.raise_for_status()
                result = response.json()
                if result.get('success'):
                    logging.info(f"TextBelt: Message sent successfully to {recipient}")
                    return True
                else:
                    logging.error(f"TextBelt: Message failed to send to {recipient}: {result.get('error')}")
                    return False

            elif self.api_service == 'twilio':
                from twilio.rest import Client
                # API key is expected as 'Account SID:Auth Token'
                sid, token = self.api_key.split(':')
                client = Client(sid, token)
                message_resp = client.messages.create(
                    to=recipient,
                    from_=self.sender_id,
                    body=message)
                logging.info(f"Twilio: Message sent successfully to {recipient}, SID: {message_resp.sid}")
                return True

            else:
                logging.error(f"Unsupported API service: {self.api_service}")
                return False

        except requests.exceptions.RequestException as e:
            logging.error(f"Request Exception: {e}")
            return False
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return False

    def process_messages(self, recipients, message):
        """
        Sends the same message to multiple recipients.
        """
        successful_sends = 0
        failed_sends = 0

        for recipient in recipients:
            start_time = time.time()
            success = self.send_sms(recipient, message)

            if success:
                successful_sends += 1
            else:
                failed_sends += 1

            elapsed_time = time.time() - start_time
            sleep_time = max(0, self.rate_limit - elapsed_time)
            time.sleep(sleep_time)

        logging.info(f"Finished processing. Successful: {successful_sends}, Failed: {failed_sends}")

    def bulk_send_messages(self, recipients, messages):
        """
        Sends different messages to different recipients.
        """
        if len(recipients) != len(messages):
            logging.error("Number of recipients and messages must match.")
            return

        successful_sends = 0
        failed_sends = 0

        for recipient, message in zip(recipients, messages):
            start_time = time.time()
            success = self.send_sms(recipient, message)

            if success:
                successful_sends += 1
            else:
                failed_sends += 1

            elapsed_time = time.time() - start_time
            sleep_time = max(0, self.rate_limit - elapsed_time)
            time.sleep(sleep_time)

        logging.info(f"Finished bulk processing. Successful: {successful_sends}, Failed: {failed_sends}")

if __name__ == '__main__':
    print(BANNER)
    # Usage example using environment variables
    api_service = os.getenv('SMS_API_SERVICE', 'textbelt')
    api_key = os.getenv('SMS_API_KEY', 'textbelt')  # Use 'textbelt' for free tier
    sender_id = os.getenv('SMS_SENDER_ID', '')

    # Try to load numbers from numbers.txt
    numbers_file = os.path.join(os.path.dirname(__file__), 'numbers.txt')
    if os.path.exists(numbers_file):
        with open(numbers_file, 'r') as f:
            recipient_list = [line.strip() for line in f if line.strip()]
    else:
        recipient_list = os.getenv('SMS_RECIPIENTS', '').split(',')

    # Try to load message from message.txt
    message_file = os.path.join(os.path.dirname(__file__), 'message.txt')
    if os.path.exists(message_file):
        with open(message_file, 'r') as f:
            message_text = f.read().strip()
    else:
        message_text = os.getenv('SMS_MESSAGE', 'Hello from MagxxxicVot SMS XII V6!')

    if not recipient_list or not recipient_list[0]:
        logging.error("No recipients configured. Set SMS_RECIPIENTS environment variable or populate numbers.txt.")
    else:
        sms_sender = SMSSender(api_service, api_key, sender_id)
        sms_sender.process_messages(recipient_list, message_text)
