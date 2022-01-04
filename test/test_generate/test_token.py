"""Tests for ``otter.generate.token``"""

from unittest import mock

from otter.generate.token import APIClient


client = APIClient("token1")


# This method will be used by the mock to replace requests.post
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.text = json_data
            self.status_code = status_code

        def json(self):
            return self.text

    return MockResponse({"token": "value1"}, 200)


@mock.patch("otter.generate.token.getpass.getpass")
@mock.patch.object(APIClient, "post")
@mock.patch('builtins.input', return_value='user')
def test_get_token(mocked_getpass, mocked_post, _):
    """
    Tests happy path for ``otter.generate.token.APIClient.get_token``, which asks the user for their
    credentials.
    """
    mocked_post.return_value = mocked_requests_post()
    mocked_getpass.return_value = "password"
    token = client.get_token()
    assert mocked_post.return_value.status_code == 200
    assert token == 'value1'


@mock.patch.object(APIClient, "post")
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data="data")
def test_upload_pdf(mocked_post, _):
    """
    Tests happy path for ``otter.generate.token.APIClient.upload_pdf``.
    """
    mocked_post.return_value = mocked_requests_post()
    client.upload_pdf_submission('123', '1', 'email', 'file.txt')
    assert mocked_post.return_value.status_code == 200


@mock.patch.object(APIClient, "post")
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data="data")
def test_replace_pdf(mocked_post, _):
    """
    Tests happy path for ``otter.generate.token.APIClient.replace_pdf``.
    """
    mocked_post.return_value = mocked_requests_post()
    client.replace_pdf_submission('123', '1', 'email', 'file.txt')
    assert mocked_post.return_value.status_code == 200


@mock.patch.object(APIClient, "post")
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data="data")
def test_upload_programming(mocked_post, _):
    """
    Tests happy path for ``otter.generate.token.APIClient.upload_programming_submission``.
    """
    mocked_post.return_value = mocked_requests_post()
    client.upload_programming_submission('123', '1', 'email', ['python.py', 'nb.ipynb'])
    assert mocked_post.return_value.status_code == 200


# TODO: do any of these tests even check that the *correct* request is being sent out?
