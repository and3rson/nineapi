from unittest import TestCase
from nineapi.client import Client, APIException
import os
import sys
import keyring

#While using the program the follwing command should be run only once,the system will store the creds.
keyring.set_password('9gag',username,password)

class APITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = username
        self.password = keyring.get_password('9gag',username)

    def test_log_in_good(self):
        response = self.client.log_in(self.username, self.password)
        self.assertEqual(response, True)

    def test_log_in_bad(self):
        self.assertRaises(APIException, lambda: self.client.log_in(self.username, self.password + 'wrong'))

    def test_get_posts(self):
        self.test_log_in_good()
        posts = self.client.get_posts()
        self.assertEqual(len(posts), 10)

#Delete keyring since it is for test only
keyring.delete_password('9gag',username)