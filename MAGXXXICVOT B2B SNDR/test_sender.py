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
                "attachment_output_formats": ["pdf"]
            }
        }

    @patch('sender.HTMLConverter.convert', new_callable=AsyncMock)
    @patch('smtplib.SMTP')
    def test_send_email_html_conversion(self, mock_smtp, mock_convert):
        mock_convert.return_value = ["test.pdf"]

        # Create a dummy test.html
        with open("test.html", "w") as f:
            f.write("<html></html>")

        success, subject = sender.send_email(self.config, "r@ex.com", "Ctx")

        self.assertTrue(success)
        # Check if convert was called
        mock_convert.assert_called()

        # Cleanup
        if os.path.exists("test.html"):
            os.remove("test.html")

    @patch('smtplib.SMTP')
    def test_send_attachments_toggle(self, mock_smtp):
        self.config['email']['send_attachments'] = False
        success, subject = sender.send_email(self.config, "r@ex.com", "Ctx")
        self.assertTrue(success)
        # Should return immediately without calling SMTP if we're simulating send,
        # but in our current implementation it returns True, subject before SMTP setup.
        self.assertFalse(mock_smtp.called)

    @patch('requests.get')
    def test_discover_server_settings(self, mock_get):
        mock_get.return_value.status_code = 404
        imap, smtp = sender.discover_server_settings("u@e.com")
        self.assertEqual(imap['host'], 'imap.e.com')

if __name__ == '__main__':
    unittest.main()
