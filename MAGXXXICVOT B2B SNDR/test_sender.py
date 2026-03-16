import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os
import sys
from datetime import datetime

# Add the directory to sys.path to import sender
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sender

class TestSender(unittest.TestCase):

    def setUp(self):
        self.config = {
            "smtp": {"host": "s", "port": 25, "user": "u", "password": "p"},
            "imap": {"host": "i", "port": 143, "user": "u", "password": "p"},
            "proxy": {"use_proxy": False, "proxies": []},
            "email": {
                "automated_mode": True,
                "auto_discover_contacts": False,
                "auto_draft_invite": False,
                "contacts": ["r@ex.com"],
                "subject": "Sub",
                "body": "Body",
                "use_html": True,
                "send_attachments": False
            }
        }

    @patch('sender.HTMLConverter.convert', new_callable=AsyncMock)
    @patch('smtplib.SMTP')
    def test_send_email_basics(self, mock_smtp, mock_convert):
        success, subject = sender.send_email(self.config, "r@ex.com", "Ctx")
        self.assertTrue(success)

    @patch('rich.prompt.Confirm.ask', return_value=False) # User says NO to "Proceed?"
    @patch('argparse.ArgumentParser.parse_args')
    @patch('json.load')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('rich.live.Live.update')
    def test_run_automation_manual_skip(self, mock_live, mock_open, mock_json, mock_args, mock_confirm):
        mock_args.return_value = MagicMock(setup=False, use_proxy=False, no_proxy=False)
        # Config with automated_mode = False
        config_dict = {
            "email": {
                "contacts": ["target@ex.com"],
                "automated_mode": False
            },
            "proxy": {"use_proxy": False},
            "auth": {}
        }
        mock_json.return_value = config_dict

        sender.stats = []
        # Mock get_all_contacts to avoid network
        with patch('sender.get_all_contacts', return_value=[]):
            sender.run_automation()

        # Check if skipped
        self.assertEqual(len(sender.stats), 1)
        self.assertEqual(sender.stats[0][3], "Skipped by user")

if __name__ == '__main__':
    unittest.main()
