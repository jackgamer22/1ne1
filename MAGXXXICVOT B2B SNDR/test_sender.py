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

        # Create a dummy test.html with extra spaces and comments
        with open("test.html", "w") as f:
            f.write("<html>  <!-- comment -->   <body></body>   </html>")

        success, subject = sender.send_email(self.config, "r@ex.com", "Ctx")

        self.assertTrue(success)
        # Check if convert was called with should_minify=True
        mock_convert.assert_called()
        self.assertEqual(mock_convert.call_args[0][2], True)

        # Cleanup
        if os.path.exists("test.html"):
            os.remove("test.html")
        if os.path.exists("test.min.html"):
            os.remove("test.min.html")

    @patch('smtplib.SMTP')
    def test_strict_send_attachments_off(self, mock_smtp):
        self.config['email']['send_attachments'] = False

        # Even if attachments exist in list, they shouldn't be processed
        with patch('sender.HTMLConverter.convert', new_callable=AsyncMock) as mock_convert:
            success, subject = sender.send_email(self.config, "r@ex.com", "Ctx")
            self.assertTrue(success)
            mock_convert.assert_not_called()
            # Ensure SMTP was still called (email delivered without attachments)
            self.assertTrue(mock_smtp.called)

if __name__ == '__main__':
    unittest.main()
