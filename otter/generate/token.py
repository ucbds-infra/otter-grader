"""
Gradescope token generator; original script provided by Gradescope
"""

import requests
import getpass

BASE_URL = 'https://www.gradescope.com'

class APIClient:
    """
    Client for Gradescope's API. Logs in users and retrieves token, uploads PDF and code assignment
    submissions. 
    
    Client code originally provided by Gradescope.

    Args:
        token (``str``, optional): a pre-retrieved token for the client
    """
    def __init__(self, token=None):
        self.session = requests.Session()
        if token is not None:
            self.token = token

    @classmethod
    def get_token(cls):
        client = cls()
        email = input("Please provide the email address on your Gradescope account: ")
        password = getpass.getpass('Password: ')
        client.log_in(email, password)
        return client.token

    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    def log_in(self, email, password):
        url = "{base}/api/v1/user_session".format(base=BASE_URL)

        form_data = {
            "email": email,
            "password": password
        }
        r = self.post(url, data=form_data)
        assert r.status_code ==  200, r.text

        self.token = r.json()['token']

    def upload_pdf_submission(self, course_id, assignment_id, student_email, filename):
        url = "{base}/api/v1/courses/{0}/assignments/{1}/submissions".format(
            course_id, assignment_id, base=BASE_URL
        )

        form_data = {
            "owner_email": student_email
        }
        files = {'pdf_attachment': open(filename, 'rb')}

        request_headers = {'access-token': self.token}
        r = self.post(url, data=form_data, headers=request_headers, files=files)
        return r

    def replace_pdf_submission(self, course_id, assignment_id, student_email, filename):
        url = "{base}/api/v1/courses/{0}/assignments/{1}/submissions/replace_pdf".format(
            course_id, assignment_id, base=BASE_URL
        )

        form_data = {
            "owner_email": student_email
        }
        files = {'pdf_attachment': open(filename, 'rb')}

        request_headers = {'access-token': self.token}
        r = self.post(url, data=form_data, headers=request_headers, files=files)
        return r

    def upload_programming_submission(self, course_id, assignment_id, student_email, filenames):
        url = "{base}/api/v1/courses/{0}/assignments/{1}/submissions".format(
            course_id, assignment_id, base=BASE_URL
        )

        form_data = {
            "owner_email": student_email
        }
        files = [('files[]', (filename, open(filename, 'rb'))) for filename in filenames]

        request_headers = {'access-token': self.token}
        r = self.post(url, data=form_data, headers=request_headers, files=files)
        return r

def main(args):
    """
    Runs ``otter generate token``
    """
    client = APIClient()
    email = input("Please provide the email address on your Gradescope account: ")
    password = getpass.getpass('Password: ')
    client.log_in(email, password)
    print("Your token is:\n", client.token)
    # Use the APIClient to upload submissions after logging in, e.g:
    # client.upload_pdf_submission(1234, 5678, 'student@example.edu', 'submission.pdf')
    # client.upload_programming_submission(1234, 5678, 'student@example.edu', ['README.md', 'src/calculator.py'])
    # You can get course and assignment IDs from the URL, e.g.
    # https://www.gradescope.com/courses/1234/assignments/5678
    # course_id = 1234, assignment_id = 5678
