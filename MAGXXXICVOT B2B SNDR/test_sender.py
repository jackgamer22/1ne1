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
            "proxy": {
                "use_proxy": True,
                "proxies": ["socks5://p1:1080"]
            },
            "email": {
                "auto_discover_contacts": True,
                "auto_draft_invite": True,
                "contacts": ["e@ex.com"],
                "subject": "Sub {{ context }}",
                "invite_template": "Invite {{ context }}",
                "body": "Body",
                "use_html": True,
                "attachments": []
            }
        }

    @patch('requests.get')
    @patch('socks.set_default_proxy')
    def test_proxy_manager_validation(self, mock_socks, mock_requests):
        mock_requests.return_value.status_code = 200
        mock_requests.return_value.text = "1.2.3.4"

        pm = sender.ProxyManager(["socks5://proxy1:1080"])
        success = pm.validate_proxies()

        self.assertTrue(success)
        self.assertEqual(len(pm.valid_proxies), 1)
        self.assertEqual(pm.get_next_proxy(), "socks5://proxy1:1080")

    @patch('smtplib.SMTP')
    @patch('socks.set_default_proxy')
    def test_send_email_with_proxy(self, mock_socks, mock_smtp):
        pm = MagicMock()
        pm.get_next_proxy.return_value = "socks5://p1:1080"

        success, subject = sender.send_email(self.config, "r@ex.com", "Context", proxy_manager=pm)

        self.assertTrue(success)
        pm.apply_proxy.assert_called_with("socks5://p1:1080")
        # Ensure socks was called
        self.assertTrue(mock_socks.called)

    @patch('sender.ProxyManager.validate_proxies', return_value=True)
    @patch('sender.get_all_contacts', return_value=[])
    @patch('sender.get_conversation_context', return_value="C")
    @patch('sender.send_email', return_value=(True, "S"))
    @patch('sender.move_sent_email', return_value="M")
    @patch('time.sleep', return_value=None)
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"proxy": {"use_proxy": true, "proxies": ["p"]}, "email": {"contacts": ["r"]}, "smtp": {}, "imap": {}}')
    @patch('rich.live.Live.update')
    def test_run_automation_proxy_flow(self, mock_live, mock_file, mock_sleep, mock_move, mock_send, mock_context, mock_discover, mock_valid):
        sender.stats = []
        sender.run_automation()
        self.assertTrue(mock_valid.called)
        self.assertTrue(mock_send.called)

if __name__ == '__main__':
    unittest.main()
