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
            "dkim": {
                "use_dkim": True,
                "selector": "default",
                "domain": "example.com",
                "private_key_path": "test.key"
            },
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

    @patch('dkim.sign')
    @patch('builtins.open', new_callable=MagicMock)
    def test_sign_message(self, mock_open, mock_dkim_sign):
        mock_open.return_value.__enter__.return_value.read.return_value = b"private_key_data"
        mock_dkim_sign.return_value = b"DKIM-Signature: sig_data"

        msg = MagicMock()
        msg.as_bytes.return_value = b"message_data"

        signed_msg = sender.sign_message(msg, self.config['dkim'])

        self.assertTrue(mock_dkim_sign.called)
        msg.add_header.assert_called_with("DKIM-Signature", "sig_data")

    @patch('argparse.ArgumentParser.parse_args')
    @patch('json.load')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('sender.interactive_settings')
    def test_run_automation_setup_flow(self, mock_interactive, mock_open, mock_json, mock_args):
        mock_args.return_value = MagicMock(setup=True, use_proxy=False, no_proxy=False)
        mock_json.return_value = {"email": {"contacts": []}}
        with patch('sender.get_all_contacts', return_value=[]):
            sender.run_automation()
        self.assertTrue(mock_interactive.called)

if __name__ == '__main__':
    unittest.main()
