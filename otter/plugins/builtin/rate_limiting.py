"""
Plugin for using Google Sheets to override scores for test cases
"""

import datetime as dt

from ..abstract_plugin import AbstractOtterPlugin


STRPTIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"


class RateLimiting(AbstractOtterPlugin):
    """
    
    """

    PLUGIN_CONFIG_KEY = "rate_limiting"

    def _window_to_str(self):
        """
        """
        result = ""
        for base in ["weeks", "days", "hours", "minutes", "seconds", "microseconds", "milliseconds"]:
            if self.plugin_config.get(base, 0):
                result += f"{self.plugin_config.get(base, 0)} {base} "
        return result.strip()

    def _submission_allowed():
        window = dt.timedelta(
            self.plugin_config.get("days", 0),
            self.plugin_config.get("seconds", 0),
            self.plugin_config.get("microsends", 0),
            self.plugin_config.get("milliseconds", 0),
            self.plugin_config.get("minutes", 0),
            self.plugin_config.get("hours", 0),
            self.plugin_config.get("weeks", 0),
        )

        subm_time = dt.datetime.strptime(self.submission_metadata["created_at"], STRPTIME_FORMAT)

        prev_subms = 0
        for subm in self.submission_metadata["previous_submissions"]:
            st = dt.datetime.strptime(subm["submission_time"], STRPTIME_FORMAT)
            if subm_time - st <= window:
                prev_subms += 1

        if prev_subms >= self.plugin_config["allowed_submissions"]:
            return False, \
                f"You have exceeded the rate limit for the autograder. Students are allowed {self.plugin_config['allowed_submissions']} " + \
                f"submissions every {self._window_to_str()}."

        else:
            return True, \
                f"Students are allowed {self.plugin_config['allowed_submissions']} every {self._window_to_str()}. " + \
                f"You have {prev_subms} submissions in that period."

    def after_grading(self, results):
        """
        """
        allowed, output = self._submission_allowed()
        results.set_output(output)
        if not allowed:
            results.hide_everything()

    def generate_report(self):
        return self._submission_allowed()[1]
