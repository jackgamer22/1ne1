import unittest
from unittest.mock import MagicMock, patch
from sms_sender import SMSSender

class TestSMSSender(unittest.TestCase):

    def setUp(self):
        self.api_service = 'textbelt'
        self.api_key = 'test_key'
        self.sender_id = 'test_sender'
        self.sms_sender = SMSSender(self.api_service, self.api_key, self.sender_id)

    @patch('requests.Session.post')
    def test_send_sms_textbelt_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        recipient = '+1234567890'
        message = 'Hello world!'

        success, detail = self.sms_sender.send_sms(recipient, message)

        self.assertTrue(success)
        self.assertEqual(detail, "Success")
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_send_sms_textbelt_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': False, 'error': 'Invalid API key'}
        mock_post.return_value = mock_response

        recipient = '+1234567890'
        message = 'Hello world!'

        success, detail = self.sms_sender.send_sms(recipient, message)

        self.assertFalse(success)
        self.assertEqual(detail, 'Invalid API key')

    @patch('twilio.rest.Client')
    def test_send_sms_twilio_success(self, mock_twilio_client):
        self.sms_sender.api_service = 'twilio'
        self.sms_sender.api_key = 'account_sid:auth_token'

        mock_client_instance = mock_twilio_client.return_value
        mock_message_resp = MagicMock()
        mock_message_resp.sid = 'SM12345'
        mock_client_instance.messages.create.return_value = mock_message_resp

        recipient = '+1234567890'
        message = 'Hello world!'

        success, detail = self.sms_sender.send_sms(recipient, message)

        self.assertTrue(success)
        self.assertEqual(detail, "SID: SM12345")

    @patch('requests.Session.post')
    def test_process_messages(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        recipients = ['+1234567890', '+0987654321']
        message = 'Hello all!'

        self.sms_sender.rate_limit = 0
        mock_live = MagicMock()
        self.sms_sender.process_messages(recipients, message, live=mock_live)

        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(mock_live.update.call_count, 2)

    @patch('requests.Session.post')
    def test_bulk_send_messages(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        recipients = ['+1234567890', '+0987654321']
        messages = ['Hello Alice!', 'Hello Bob!']

        self.sms_sender.rate_limit = 0
        mock_live = MagicMock()
        self.sms_sender.bulk_send_messages(recipients, messages, live=mock_live)

        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(mock_live.update.call_count, 2)

if __name__ == '__main__':
    # Add activation token to env for tests
    import os
    os.environ['ACTIVATION_TOKEN'] = 'MAGXXXICVOT-MASTER-2026'
    unittest.main()
