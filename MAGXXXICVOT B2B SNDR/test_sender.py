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
    def test_discover_server_settings_success(self, mock_get):
        xml_content = """
        <clientConfig version="1.1">
          <emailProvider id="example.com">
            <incomingServer type="imap">
              <hostname>imap.example.com</hostname>
              <port>993</port>
              <socketType>SSL</socketType>
            </incomingServer>
            <outgoingServer type="smtp">
              <hostname>smtp.example.com</hostname>
              <port>587</port>
              <socketType>STARTTLS</socketType>
            </outgoingServer>
          </emailProvider>
        </clientConfig>
        """
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = xml_content.encode()

        imap, smtp = sender.discover_server_settings("test@example.com")

        self.assertEqual(imap['host'], 'imap.example.com')
        self.assertEqual(smtp['host'], 'smtp.example.com')
        self.assertTrue(imap['use_ssl'])
        self.assertTrue(smtp['use_tls'])

    @patch('requests.get')
    def test_discover_server_settings_fallback(self, mock_get):
        mock_get.return_value.status_code = 404

        imap, smtp = sender.discover_server_settings("test@randomdomain.com")

        self.assertEqual(imap['host'], 'imap.randomdomain.com')
        self.assertEqual(smtp['host'], 'smtp.randomdomain.com')

    @patch('sender.discover_server_settings', return_value=({"host": "i"}, {"host": "s"}))
    @patch('argparse.ArgumentParser.parse_args')
    @patch('json.load')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('sender.get_all_contacts', return_value=[])
    @patch('sender.get_conversation_context', return_value="C")
    @patch('sender.send_email', return_value=(True, "S"))
    @patch('sender.move_sent_email', return_value="M")
    @patch('time.sleep', return_value=None)
    @patch('rich.live.Live.update')
    def test_run_automation_auto_discovery_trigger(self, mock_live, mock_sleep, mock_move, mock_send, mock_context, mock_discover, mock_open, mock_json_load, mock_args, mock_valid_disc):
        mock_args.return_value = MagicMock(use_proxy=False, no_proxy=True)
        # Config with auth but no imap/smtp
        config_dict = {"auth": {"email": "u@e.com", "password": "p", "auto_discovery": True}, "email": {"contacts": ["r"]}, "proxy": {}}
        mock_json_load.return_value = config_dict

        sender.stats = []
        sender.run_automation()

        self.assertTrue(mock_valid_disc.called)

if __name__ == '__main__':
    unittest.main()
