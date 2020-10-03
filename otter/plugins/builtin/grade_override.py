"""
Plugin for using Google Sheets to override scores for test cases
"""

import json
import tempfile
import gspread
import pandas as pd

from ..abstract_plugin import AbstractOtterPlugin


class GoogleSheetsGradeOverride(AbstractOtterPlugin):
    """
    Otter plugin for overriding test case scores with values in a Google Sheet on Gradescope. Uses 
    provided Google Service Account credentials to pull in the spreadsheet as a dataframe and edits
    test case scores by matching on the Gradescope assignment ID, student email, and test case name.

    Implements the ``during_generate`` and ``after_grading`` events. For plugin configurations, use
    key ``google_sheets_grade_override``. 
    
    The google sheet should have the following format:

    | Assignment ID | Email            | Test Case | Points |
    |---------------|------------------|-----------|--------|
    | 123456        | student@univ.edu | q1a - 1   | 1      |

    ``Assignment ID`` should be the ID of the assignment on Gradescope, ``Email`` should be the email
    address corresponding to the student's Gradescope account, ``Test Case`` should be the name of
    the test case, and ``Points`` should be the number of points that the student should be assigned.
    """

    PLUGIN_CONFIG_KEY = "google_sheets_grade_override"

    def _load_df(self):
        oauth_json = self.plugin_config["service_account_credentials"]
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as ntf:
            json.dump(oauth_json, ntf)
            ntf.seek(0)

            gc = gspread.service_account(filename=ntf.name)
        
        sheet_url = self.plugin_config["sheet_url"]
        sheet = gc.open_by_url(sheet_url)
        worksheet = sheet.get_worksheet(0)
        data = worksheet.get_all_values()
        colnames = data.pop(0)

        df = pd.DataFrame(data, columns=colnames)
        return df

    def after_grading(self, results):
        """
        Modifies the results of grading by pulling in the Google Sheet as a dataframe and updating 
        the scores for the test cases found.
        """
        df = self._load_df()
        df = df[
            df["Email"].isin([user["email"] for user in self.submission_metadata["users"]]) & \
            (df["Assignment ID"] == str(self.submission_metadata["assignment"]["id"]))
        ]
        for _, row in df.iterrows():
            results.update_result(row["Test Case"], score=row["Points"])

    def during_generate(self, otter_config):
        """
        Takes a path to Google Service Account credentials stored in this plugin's config as key
        ``credentials_json_path`` and extracts the data from that file into the plugin's config as key
        ``service_account_credentials``.
        """
        creds_path = otter_config["plugin_config"][self.PLUGIN_CONFIG_KEY]["credentials_json_path"]
        with open(creds_path) as f:
            creds = json.load(f)
        otter_config["plugin_config"][self.PLUGIN_CONFIG_KEY]["service_account_credentials"] = creds
