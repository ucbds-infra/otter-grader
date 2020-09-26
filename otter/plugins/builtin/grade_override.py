import json
import tempfile
import gspread
import pandas as pd

from ..abstract_plugin import AbstractOtterPlugin


class GoogleSheetGradeOverridePlugin(AbstractOtterPlugin):

    PLUGIN_CONFIG_KEY = "regrade_google_sheets"

    def _load_df(self):
        oauth_json = self.plugin_config["service_account_credentials"]
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as ntf:
            json.dump(oauth_json, ntf)

            gc = gspread.service_account(filename=ntf.name)
        
        sheet_url = self.plugin_config["sheet_url"]
        sheet = gc.open_by_url(sheet_url)
        worksheet = sheet.get_worksheet(0)
        data = worksheet.get_all_values()
        colnames = data.pop(0)

        df = pd.DataFrame(data, columns=colnames)
        return df

    # | Assignment ID | Email            | Test Case | Points |
    # |---------------|------------------|-----------|--------|
    # | 123456        | student@univ.edu | q1a - 1   | 1      |

    def after_grading(self, results):
        df = self._load_df()
        df = df[
            df["Email"].isin([user["email"] for user in self.submission_metadata["users"] & \
            df["Assignment ID"] == self.submission_metadata["assignment"]["id"]
        ])]
        for _, row in df.iterrows():
            results.update_result(row["Test Case"], score=row["Points"])

    def during_generate(self, otter_config):
        creds_path = otter_config["plugin_config"][self.PLUGIN_CONFIG_KEY]["credentials_json_path"]
        with open(creds_path) as f:
            creds = json.load(f)
        otter_config["plugin_config"][self.PLUGIN_CONFIG_KEY]["service_account_credentials"] = creds
