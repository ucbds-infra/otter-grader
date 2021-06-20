"""
Plugin for using the Gmail API to notify students about the results of public test cases
"""

import os
import json
import tempfile
import gspread
import pandas as pd
import base64
import google.oauth2.credentials

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from jinja2 import Template
from textwrap import dedent

from ... import PluginCollection
from ...abstract_plugin import AbstractOtterPlugin


SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailNotifications(AbstractOtterPlugin):
    """
    Otter plugin for sending students an email notification with the results of their public test
    cases. Uses the Gmail API along with user-specified credentials a Google OAuth2 Client to send
    the emails once grading is finished.

    This plugin requires the following configurations:

    - ``client_id``: the Google OAuth2 Client ID
    - ``client_secret``: the Google OAuth2 Client secret
    - ``refresh_tokem``: the Google OAuth2 Client refresh token; more information below
    - ``email``: the email address to send from

    It also supports the following optional configurations:

    - ``catch_api_error``: if this configuration is true, errors thrown by Google API calls are ignored;
      if false, the errors are raised and the grading process stops; defaults to ``True``
    """

    IMPORTABLE_NAME = "otter.plugins.builtin.GmailNotifications"

    email_template_html = Template(dedent("""\
        <p>Hello {{ student_name }},</p>

        <p>Your submission {% if zip_name %}<code>{{ zip_name }}</code>{% endif %} for assignment 
        <strong>{{ assignment_title }}</strong> submitted at {{ submission_timestamp }} received the 
        following scores on public tests:</p>

        <pre>{{ score_report }}</pre>

        <p>If you have any questions or notice any issues, please contact your instructors.</p>

        <hr>

        <p>This message was automatically generated by Otter-Grader.</p>
    """))

    email_template_plain = Template(dedent("""\
        Hello {{ student_name }},

        Your submission {% if zip_name %}{{ zip_name }}{% endif %} for assignment {{ assignment_title }} 
        submitted at {{ submission_timestamp }} received the following scores on public tests:

        {{ score_report }}

        If you have any questions or notice any issues, please contact your instructors.

        ---

        This message was automatically generated by Otter-Grader.
    """))

    def _authenticate(self):
        """
        Create a Google API service using the client ID, secret, and refresh token in the plugin
        configurations.
        """
        try:
            credentials = google.oauth2.credentials.Credentials(
                'token',
                refresh_token=self.plugin_config["refresh_token"],
                token_uri='https://accounts.google.com/o/oauth2/token',
                client_id=self.plugin_config["client_id"],
                client_secret=self.plugin_config["client_secret"],
            )
            self._service = build('gmail', 'v1', credentials=credentials, cache_discovery=False)

        except Exception as e:
            if self.plugin_config.get("catch_api_error", True):
                print(f"Error encountered while authenticating with Gmail:\n{e}")
            else:
                raise e

    @property
    def service(self):
        """
        The Google API service
        """
        if not hasattr(self, "_service") or self._service is None:
            self._authenticate()
        return self._service

    def after_grading(self, results):
        """
        Summarizes the results of grading and formats an email to send to the student using the
        submission metadata. If not submission metadata is supplied, no action is taken.

        Args:
            results (``otter.test_files.GradingResults``): the results of grading
        """
        from ....check.notebook import _ZIP_NAME_FILENAME
        if os.path.exists(_ZIP_NAME_FILENAME):
            with open(_ZIP_NAME_FILENAME) as f:
                zip_name = f.read().strip()
        else:
            zip_name = None
        if self.submission_metadata:
            for user in self.submission_metadata["users"]:
                email_contents = self.email_template_plain.render({
                    "student_name": user["name"],
                    "assignment_title": self.submission_metadata["assignment"]["title"],
                    "submission_timestamp": self.submission_metadata["created_at"],
                    "score_report": results.summary(public_only=True),
                    "zip_name": zip_name,
                })
                plain_email = MIMEText(email_contents, _subtype="plain")

                email_contents = self.email_template_html.render({
                    "student_name": user["name"],
                    "assignment_title": self.submission_metadata["assignment"]["title"],
                    "submission_timestamp": self.submission_metadata["created_at"],
                    "score_report": results.summary(public_only=True),
                    "zip_name": zip_name,
                })
                html_email = MIMEText(email_contents, _subtype="html")

                message = MIMEMultipart('alternative')
                message.attach(plain_email)
                message.attach(html_email)
                message["subject"] = f'Autograder Results for { self.submission_metadata["assignment"]["title"] }'
                message["to"] = user["email"]
                message["from"] = self.plugin_config["email"]
                msg = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

                try:
                    message = self.service.users().messages().send(userId='me', body=msg).execute()
                except Exception as e:
                    if self.plugin_config.get("catch_api_error", True):
                        print(f'An error occurred while emailing results:\n{e}')
                    else:
                        raise e