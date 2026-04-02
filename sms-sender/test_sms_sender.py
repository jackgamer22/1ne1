import unittest
from unittest.mock import MagicMock, patch
from sms_sender import SMSSender
import requests

class TestSMSSender(unittest.TestCase):

    def setUp(self):
        self.api_service = 'textbelt'
        self.api_key = 'test_key'
        self.sender_id = 'test_sender'
        self.sms_sender = SMSSender(self.api_service, self.api_key, self.sender_id)

    @patch('requests.Session.post')
    def test_send_sms_textbelt_success(self, mock_post):
        # Mock successful response from TextBelt
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        recipient = '+1234567890'
        message = 'Hello world!'

        result = self.sms_sender.send_sms(recipient, message)

        self.assertTrue(result)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['data']['phone'], recipient)
        self.assertEqual(kwargs['data']['message'], message)
        self.assertEqual(kwargs['data']['key'], self.api_key)

    @patch('requests.Session.post')
    def test_send_sms_textbelt_failure(self, mock_post):
        # Mock failed response from TextBelt
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': False, 'error': 'Invalid API key'}
        mock_post.return_value = mock_response

        recipient = '+1234567890'
        message = 'Hello world!'

        result = self.sms_sender.send_sms(recipient, message)

        self.assertFalse(result)

    @patch('twilio.rest.Client')
    def test_send_sms_twilio_success(self, mock_twilio_client):
        # Mock Twilio client and response
        self.sms_sender.api_service = 'twilio'
        self.sms_sender.api_key = 'account_sid:auth_token'

        mock_client_instance = mock_twilio_client.return_value
        mock_message_resp = MagicMock()
        mock_message_resp.sid = 'SM12345'
        mock_client_instance.messages.create.return_value = mock_message_resp

        recipient = '+1234567890'
        message = 'Hello world!'

        result = self.sms_sender.send_sms(recipient, message)

        self.assertTrue(result)
        mock_client_instance.messages.create.assert_called_once_with(
            to=recipient,
            from_=self.sender_id,
            body=message
        )

    @patch('requests.Session.post')
    def test_process_messages(self, mock_post):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        recipients = ['+1234567890', '+0987654321']
        message = 'Hello all!'

        # Set rate_limit to 0 for faster testing
        self.sms_sender.rate_limit = 0
        self.sms_sender.process_messages(recipients, message)

        self.assertEqual(mock_post.call_count, 2)

    @patch('requests.Session.post')
    def test_bulk_send_messages(self, mock_post):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        recipients = ['+1234567890', '+0987654321']
        messages = ['Hello Alice!', 'Hello Bob!']

        # Set rate_limit to 0 for faster testing
        self.sms_sender.rate_limit = 0
        self.sms_sender.bulk_send_messages(recipients, messages)

        self.assertEqual(mock_post.call_count, 2)

if __name__ == '__main__':
    unittest.main()
