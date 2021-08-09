####################################
##### Tests for otter generate #####
####################################
import os
import unittest
import subprocess
import json
import shutil
import requests
import getpass

from subprocess import PIPE
from glob import glob
from unittest.mock import patch, mock_open
from shutil import copyfile

from otter.generate.token import APIClient

from .. import TestCase


client = APIClient('token1')


# mock input
def get_input(text):
    return input(text)


# This method will be used by the mock to replace requests.post
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.text = json_data
            self.status_code = status_code

        def json(self):
            return self.text

    return MockResponse({"token": "value1"}, 200)


class TestToken(TestCase):

    @patch.object(getpass,"getpass")
    @patch.object(APIClient,"post")
    @patch('builtins.input', return_value='user')
    def test_get_token(self, mockGetPass, mockPost, mockInput):

        """
        Tests happy path for get_token, which also logs in
        """

        mockPost.return_value = mocked_requests_post()
        mockGetPass.return_value = "password"
        token = client.get_token()
        self.assertEqual(mockPost.return_value.status_code, 200)
        self.assertEqual(token, 'value1')
    
    @patch.object(APIClient,"post")
    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_upload_pdf(self, mockPost, mockOpen):

        """
        Tests happy path for upload_pdf
        """

        mockPost.return_value = mocked_requests_post()
        client.upload_pdf_submission('123', '1', 'email', 'file.txt')
        self.assertEqual(mockPost.return_value.status_code, 200)
    

    @patch.object(APIClient,"post")
    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_replace_pdf(self, mockPost, mockOpen):

        """
        Tests happy path for replace_pdf
        """

        mockPost.return_value = mocked_requests_post()
        client.replace_pdf_submission('123', '1', 'email', 'file.txt')
        self.assertEqual(mockPost.return_value.status_code, 200)
    
    @patch.object(APIClient,"post")
    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_upload_programming(self, mockPost, mockOpen):

        """
        Tests happy path for uploading programming solns
        """

        mockPost.return_value = mocked_requests_post()
        client.upload_programming_submission('123', '1', 'email', ['python.py', 'nb.ipynb'])
        self.assertEqual(mockPost.return_value.status_code, 200)
