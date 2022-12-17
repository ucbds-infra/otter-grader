"""
Plugin for using Google Sheets to override scores for test cases
"""

import os
import json
import tempfile
import pandas as pd

from .. import PluginCollection
from ..abstract_plugin import AbstractOtterPlugin


class GoogleSheetsGradeOverride(AbstractOtterPlugin):
    """
    Otter plugin for overriding test case scores with values in a Google Sheet on Gradescope. Uses 
    provided Google Service Account credentials to pull in the spreadsheet as a dataframe and edits
    test case scores by matching on the Gradescope assignment ID, student email, and test case name.

    Implements the ``during_generate``, ``before_grading``, and ``after_grading`` events. Make sure 
    to list this plugin as ``otter.plugins.builtin.GoogleSheetsGradeOverride``, otherwise the 
    ``during_generate`` event of this plugin will not work.

    The google sheet should have the following format:

    =============== ================== =========== ======== ==============
     Assignment ID   Email              Question    Points   PDF          
    =============== ================== =========== ======== ==============
     123456          student@univ.edu   q1a - 1     1        false        
    =============== ================== =========== ======== ==============

    ``Assignment ID`` should be the ID of the assignment on Gradescope, ``Email`` should be the email
    address corresponding to the student's Gradescope account, ``Question`` should be the name of
    the question, and ``Points`` should be the number of points that the student should be assigned.
    ``PDF`` should be ``false`` if the student's PDF should *not* be regenerated during this run of
    the autograder.
    """

    IMPORTABLE_NAME = "otter.plugins.builtin.GoogleSheetsGradeOverride"

    def _load_df(self):
        """
        Uses the Google Sheets API credentials stored in ``self.plugin_config`` to read in the
        sheet using ``pandas``.

        Returns:
            ``pandas.core.frame.DataFrame``: the sheet as a dataframe
        """
        import gspread
        try:
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

            self._df = pd.DataFrame(data, columns=colnames)
        except Exception as e:
            if self.plugin_config.get("catch_api_error", True):
                print(f"Error encountered while loading grade override sheet:\n{e}")
                self._df = pd.DataFrame(columns=["Assignment ID", "Email", "Question", "Points", "PDF"])
            else:
                raise e

    @property
    def df(self):
        """
        The grade override information dataframe
        """
        if not hasattr(self, "_df") or self._df is None:
            self._load_df()
        return self._df

    def after_grading(self, results):
        """
        Modifies the results of grading by pulling in the Google Sheet as a dataframe and updating 
        the scores for the test cases found.

        Args:
            results (``otter.test_files.GradingResults``): the results of grading
        """
        if self.submission_metadata:
            df = self.df.copy()
            df = df[
                df["Email"].isin([user["email"] for user in self.submission_metadata["users"]]) & \
                (df["Assignment ID"] == str(self.submission_metadata["assignment"]["id"]))
            ]
            for _, row in df.iterrows():
                results.update_score(row["Question"], float(row["Points"]))

    def during_generate(self, otter_config, assignment):
        """
        Takes a path to Google Service Account credentials stored in this plugin's config as key
        ``credentials_json_path`` and extracts the data from that file into the plugin's config as key
        ``service_account_credentials``.

        Args:
            otter_config (``dict``): the parsed Otter configuration JSON file
            assignment (``otter.assign.assignment.Assignment``): the assignment configurations if 
                Otter Assign is used
        """
        if assignment is not None:
            curr_dir = os.getcwd()
            os.chdir(assignment.master.parent)

        cfg_idx = [self.IMPORTABLE_NAME in c.keys() for c in otter_config["plugins"] if isinstance(c, dict)].index(True)
        creds_path = otter_config["plugins"][cfg_idx][self.IMPORTABLE_NAME]["credentials_json_path"]
        with open(creds_path, encoding="utf-8") as f:
            creds = json.load(f)
        otter_config["plugins"][cfg_idx][self.IMPORTABLE_NAME]["service_account_credentials"] = creds

        if assignment is not None:
            os.chdir(curr_dir)

    def before_grading(self, config):
        """
        Controls whether or not a PDF is generated by setting the ``token`` key of the grading config
        to ``None`` if any of the rows in the dataframe matching this (email, assignment ID) tuple
        indicate that a PDF should not be generated.

        Args:
            config (``dict``): the grading configurations
        """
        if self.submission_metadata:
            df = self.df.copy()
            df = df[
                df["Email"].isin([user["email"] for user in self.submission_metadata["users"]]) & \
                (df["Assignment ID"] == str(self.submission_metadata["assignment"]["id"]))
            ]

            for _, row in df.iterrows():
                generate_pdf = row["PDF"].strip().lower()
                if generate_pdf in ["n", "false", "f", "0"]:
                    config.token = None
