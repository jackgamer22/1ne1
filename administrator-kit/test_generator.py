import hashlib
import unittest
from token_generator import generate_token

class TestTokenGenerator(unittest.TestCase):
    def test_token_match(self):
        hwid = "user-123-hwid"
        secret_salt = "magxxxicvot_secret"
        expected = hashlib.sha256((hwid + secret_salt).encode()).hexdigest()

        actual = generate_token(hwid)

        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()
