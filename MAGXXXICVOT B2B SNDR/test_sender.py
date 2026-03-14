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
                "to": "recipient@example.com",
                "subject": "Test Subject",
                "body": "Test Body"
            }
        }

    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        instance = mock_smtp.return_value
        result = sender.send_email(self.config)
        self.assertTrue(result)
        instance.login.assert_called_with("user@example.com", "password")
        instance.send_message.assert_called()

    @patch('smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        instance = mock_smtp.return_value
        instance.login.side_effect = Exception("Auth failed")
        result = sender.send_email(self.config)
        self.assertFalse(result)

    @patch('imaplib.IMAP4_SSL')
    def test_move_sent_email_success(self, mock_imap):
        instance = mock_imap.return_value
        instance.login.return_value = 'OK'
        instance.select.return_value = ('OK', [b'1'])
        instance.search.return_value = ('OK', [b'123'])
        instance.copy.return_value = ('OK', [b'Copy OK'])
        instance.store.return_value = ('OK', [b'Store OK'])

        result = sender.move_sent_email(self.config)
        self.assertTrue(result)
        instance.login.assert_called_with("user@example.com", "password")
        instance.copy.assert_called_with(b'123', 'Archive')

    @patch('imaplib.IMAP4_SSL')
    def test_move_sent_email_not_found(self, mock_imap):
        instance = mock_imap.return_value
        instance.login.return_value = 'OK'
        instance.select.return_value = ('OK', [b'1'])
        instance.search.return_value = ('OK', [b'']) # No emails found

        result = sender.move_sent_email(self.config)
        self.assertTrue(result) # Function returns True even if not found, just prints message
        instance.copy.assert_not_called()

if __name__ == '__main__':
    unittest.main()
