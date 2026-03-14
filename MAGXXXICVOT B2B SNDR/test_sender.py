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
            "smtp": {"host": "s", "port": 25, "user": "u", "password": "p"},
            "imap": {"host": "i", "port": 143, "user": "u", "password": "p"},
            "email": {
                "auto_discover_contacts": True,
                "auto_draft_invite": True,
                "contacts": ["existing@ex.com"],
                "subject": "Sub {{ context }}",
                "invite_template": "Invite {{ context }}",
                "body": "Body",
                "use_html": True,
                "attachments": []
            }
        }

    @patch('imaplib.IMAP4')
    def test_get_all_contacts(self, mock_imap_class):
        instance = mock_imap_class.return_value
        instance.login.return_value = 'OK'
        instance.select.return_value = ('OK', [b'1'])
        instance.search.return_value = ('OK', [b'1 2'])
        # Mock fetch to return a From header
        instance.fetch.return_value = ('OK', [(b'1', b'From: "John" <john@ex.com>\r\n')])

        # Override config to use IMAP4 instead of IMAP4_SSL for easier mocking if needed,
        # but let's just make sure it uses the mock.
        self.config['imap']['use_ssl'] = False

        contacts = sender.get_all_contacts(self.config)
        self.assertIn("john@ex.com", contacts)

    @patch('smtplib.SMTP')
    def test_send_email_invite_template(self, mock_smtp):
        instance = mock_smtp.return_value
        recipient = "r@ex.com"
        context = "Project X"
        success, subject = sender.send_email(self.config, recipient, context)

        self.assertTrue(success)
        call_args = instance.send_message.call_args[0][0]
        payload = call_args.get_payload()
        if isinstance(payload, list):
            html_part = payload[0].get_payload()
        else:
            html_part = payload

        # Should use invite_template instead of body when auto_draft_invite is True
        self.assertIn("Invite Project X", html_part)
        self.assertNotIn("Body", html_part)

    @patch('sender.get_all_contacts', return_value=["discovered@ex.com"])
    @patch('sender.get_conversation_context', return_value="Context")
    @patch('sender.send_email', return_value=(True, "Subject"))
    @patch('sender.move_sent_email', return_value="Moved")
    @patch('time.sleep', return_value=None)
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"email": {"auto_discover_contacts": true, "contacts": ["existing@ex.com"]}, "smtp": {}, "imap": {}}')
    @patch('rich.live.Live.update')
    def test_run_automation_with_discovery(self, mock_live, mock_file, mock_sleep, mock_move, mock_send, mock_context, mock_discover):
        sender.stats = [] # Clear stats
        sender.run_automation()
        # Should process both existing and discovered contacts
        self.assertEqual(mock_send.call_count, 2)

if __name__ == '__main__':
    unittest.main()
