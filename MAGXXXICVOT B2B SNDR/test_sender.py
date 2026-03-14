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
                "host": "smtp.ex.com",
                "port": 587,
                "user": "u@ex.com",
                "password": "p",
                "use_tls": True
            },
            "imap": {
                "host": "imap.ex.com",
                "port": 993,
                "user": "u@ex.com",
                "password": "p",
                "use_ssl": True,
                "archive_folder": "Archive"
            },
            "email": {
                "contacts": ["r1@ex.com"],
                "subject": "Sub {{ context }}",
                "body": "Body {{ context }}",
                "use_html": True,
                "logo_base64": "AAA",
                "signature": "Sig",
                "attachments": []
            }
        }

    @patch('smtplib.SMTP')
    def test_send_email_placeholders(self, mock_smtp):
        instance = mock_smtp.return_value
        recipient = "r1@ex.com"
        context = "Special Context"
        success, subject = sender.send_email(self.config, recipient, context)

        self.assertTrue(success)
        self.assertEqual(subject, "Sub Special Context")

        call_args = instance.send_message.call_args[0][0]
        self.assertEqual(call_args['Subject'], "Sub Special Context")

        payload = call_args.get_payload()
        if isinstance(payload, list):
            html_part = payload[0].get_payload()
        else:
            html_part = payload
        self.assertIn("Body Special Context", html_part)

    @patch('imaplib.IMAP4_SSL')
    def test_get_conversation_context_success(self, mock_imap):
        instance = mock_imap.return_value
        instance.login.return_value = 'OK'
        instance.select.return_value = ('OK', [b'1'])
        instance.search.return_value = ('OK', [b'10'])
        instance.fetch.return_value = ('OK', [(b'1', b'Subject: Hello World\r\n')])

        context = sender.get_conversation_context(self.config, "r1@ex.com")
        self.assertEqual(context, "Hello World")

    @patch('sender.get_conversation_context', return_value="TestContext")
    @patch('sender.send_email', return_value=(True, "Sub TestContext"))
    @patch('sender.move_sent_email', return_value="Moved")
    @patch('time.sleep', return_value=None)
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"email": {"contacts": ["r1@ex.com"]}, "smtp": {}, "imap": {}}')
    @patch('rich.live.Live.update')
    def test_run_automation_dashboard_flow(self, mock_live, mock_file, mock_sleep, mock_move, mock_send, mock_context):
        sender.run_automation()
        self.assertTrue(mock_context.called)
        self.assertTrue(mock_send.called)
        self.assertTrue(mock_move.called)
        # Check if stats were updated
        self.assertEqual(len(sender.stats), 1)
        self.assertIn("r1@ex.com", sender.stats[0])

if __name__ == '__main__':
    unittest.main()
