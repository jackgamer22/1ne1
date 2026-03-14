import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add the directory to sys.path to import sender
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sender

class TestSender(unittest.TestCase):

    def setUp(self):
        self.config = {
            "smtp": {
                "host": "smtp.example.com",
                "port": 587,
                "user": "user@example.com",
                "password": "password",
                "use_tls": True
            },
            "imap": {
                "host": "imap.example.com",
                "port": 993,
                "user": "user@example.com",
                "password": "password",
                "use_ssl": True,
                "archive_folder": "Archive"
            },
            "email": {
                "contacts": ["r1@ex.com", "r2@ex.com"],
                "subject": "Test Subject",
                "body": "Test Body",
                "logo_base64": "AAA",
                "signature": "My Sig"
            }
        }

    @patch('smtplib.SMTP')
    def test_send_email_html_content(self, mock_smtp):
        instance = mock_smtp.return_value
        recipient = "r1@ex.com"
        result = sender.send_email(self.config, recipient)
        self.assertTrue(result)

        # Verify that send_message was called with a MIMEMultipart object containing HTML
        call_args = instance.send_message.call_args[0][0]
        self.assertEqual(call_args['To'], recipient)

        # Check if HTML content is present
        payload = call_args.get_payload()
        if isinstance(payload, list):
            html_part = payload[0].get_payload()
        else:
            html_part = payload

        self.assertIn('data:image/png;base64,AAA', html_part)
        self.assertIn('My Sig', html_part)
        self.assertIn('Test Body', html_part)

    @patch('imaplib.IMAP4_SSL')
    def test_move_sent_email_success(self, mock_imap):
        instance = mock_imap.return_value
        instance.login.return_value = 'OK'
        instance.select.return_value = ('OK', [b'1'])
        instance.search.return_value = ('OK', [b'123'])
        instance.copy.return_value = ('OK', [b'Copy OK'])
        instance.store.return_value = ('OK', [b'Store OK'])

        recipient = "r1@ex.com"
        result = sender.move_sent_email(self.config, recipient)
        self.assertTrue(result)
        instance.search.assert_called()
        search_call_args = instance.search.call_args[0][1]
        self.assertIn(recipient, search_call_args)

    @patch('sender.send_email')
    @patch('sender.move_sent_email')
    @patch('time.sleep', return_value=None)
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"email": {"contacts": ["r1@ex.com", "r2@ex.com"], "subject": "S"}, "smtp": {}, "imap": {}}')
    def test_run_automation_multiple_contacts(self, mock_file, mock_sleep, mock_move, mock_send):
        mock_send.return_value = True
        sender.run_automation()
        self.assertEqual(mock_send.call_count, 2)
        self.assertEqual(mock_move.call_count, 2)

if __name__ == '__main__':
    unittest.main()
