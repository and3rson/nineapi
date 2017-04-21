from unittest import TestCase
from nineapi.client import Client, APIException
import os
import sys


for var in ('NINEGAG_USERNAME', 'NINEGAG_PASSWORD'):
    if var not in os.environ:
        sys.stderr.write('ERROR: Environment variable {} is required for the tests to run.\n'.format(
            var
        ))
        sys.exit(1)


class APITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = os.environ['NINEGAG_USERNAME']
        self.password = os.environ['NINEGAG_PASSWORD']

    def test_log_in_good(self):
        response = self.client.log_in(self.username, self.password)
        self.assertEqual(response, True)

    def test_log_in_bad(self):
        self.assertRaises(APIException, lambda: self.client.log_in(self.username, self.password + 'wrong'))

    def test_get_posts(self):
        self.test_log_in_good()
        posts = self.client.get_posts()
        self.assertEqual(len(posts), 10)
