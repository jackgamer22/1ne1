import unittest
from unittest.mock import patch, MagicMock, AsyncMock
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
            "proxy": {"use_proxy": False, "proxies": []},
            "email": {
                "auto_discover_contacts": False,
                "auto_draft_invite": False,
                "contacts": ["r@ex.com"],
                "subject": "Sub",
                "body": "Body",
                "use_html": True,
                "attachments": ["test.html"],
                "send_attachments": True,
                "convert_html_attachments": True,
                "minify_html": True,
                "attachment_output_formats": ["pdf"]
            }
        }

    @patch('sender.HTMLConverter.convert', new_callable=AsyncMock)
    @patch('smtplib.SMTP')
    def test_send_email_with_minification(self, mock_smtp, mock_convert):
        mock_convert.return_value = ["test.pdf"]
        with open("test.html", "w") as f:
            f.write("<html><body></body></html>")
        success, subject = sender.send_email(self.config, "r@ex.com", "Ctx")
        self.assertTrue(success)
        if os.path.exists("test.html"): os.remove("test.html")
        if os.path.exists("test.min.html"): os.remove("test.min.html")

    @patch('argparse.ArgumentParser.parse_args')
    @patch('json.load')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('sender.interactive_settings')
    def test_run_automation_setup_flag(self, mock_interactive, mock_open, mock_json, mock_args):
        mock_args.return_value = MagicMock(setup=True, use_proxy=False, no_proxy=False)
        mock_json.return_value = {"email": {"contacts": []}}
        # Simulate run
        with patch('sender.get_all_contacts', return_value=[]):
            sender.run_automation()
        self.assertTrue(mock_interactive.called)

if __name__ == '__main__':
    unittest.main()
