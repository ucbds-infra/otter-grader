"""
Plugin for using Google Sheets to override scores for test cases
"""

import datetime as dt

from ..abstract_plugin import AbstractOtterPlugin


STRPTIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"


class RateLimiting(AbstractOtterPlugin):
    """
    Implements submission rate limiting by restricting the number of submissions a student is allowed
    during a specified window

    This plugin is configured by defining the duration of the window using the optional keys ``weeks``,
    ``days``, ``hours``, ``minutes``, ``seconds``, ``milliseconds``, and ``microseconds`` (all of which
    default to 0). The number of submissions allowed during this window is configured with
    ``allowed_submissions``. For example, to allow only 2 submissions every hour-and-a-half:

    .. code-block:: json

        {
            "plugins": [
                {
                    "otter.plugins.builtin.RateLimiting": {
                        "hours": 1,
                        "minutes": 30,
                        "allowed_submissions": 2
                    }
                }
            ]
        }

    When a student submits, the window is caculated as a `datetime.timedelta` object and if the student
    has at least `allowed_submissions` in that window, the submission's results are hidden and the
    student is only shown a message; from the example above:

    .. code-block::

        You have exceeded the rate limit for the autograder. Students are allowed 2 submissions every 1 hours 30 minutes.

    The results of submission execution are still visible to instructors.

    If the student's submission is allowed based on the rate limit, the plugin outputs a message in
    the plugin report; from the example above:

    .. code-block::

        Students are allowed 2 submissions every 1 hours 30 minutes. You have {number of previous submissions} submissions in that period.
    """

    def _window_to_str(self):
        """
        Returns a string representation of the configured window
        """
        result = ""
        for base in [
            "weeks",
            "days",
            "hours",
            "minutes",
            "seconds",
            "microseconds",
            "milliseconds",
        ]:
            if self.plugin_config.get(base, 0):
                result += f"{self.plugin_config.get(base, 0)} {base} "
        return result.strip()

    def _submission_allowed(self):
        """
        Determines whether the rate limit was execeeded and returns a corresponding message

        Returns:
            ``tuple[bool,str]``: whether the submission is allowed and the message
        """
        window = dt.timedelta(
            self.plugin_config.get("days", 0),
            self.plugin_config.get("seconds", 0),
            self.plugin_config.get("microseconds", 0),
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
            return (
                False,
                f"You have exceeded the rate limit for the autograder. Students are allowed {self.plugin_config['allowed_submissions']} "
                + f"submissions every {self._window_to_str()}.",
            )

        else:
            return (
                True,
                f"Students are allowed {self.plugin_config['allowed_submissions']} submissions every {self._window_to_str()}. "
                + f"You have {prev_subms} submissions in that period.",
            )

    def after_grading(self, results):
        """
        Determines whether a student has exceeded the rate limit; if yes, all results are hidden from
        the student using ``otter.test_files.GradingResults.hide_everything`` and the output of the
        grader is set to the message.

        Args:
            results (``otter.test_files.GradingResults.hide_everything``): the results of grading
        """
        if self.submission_metadata:
            allowed, output = self._submission_allowed()
            results.set_output(output)
            if not allowed:
                results.hide_everything()

    def generate_report(self):
        """
        Returns the message regarding whether the rate limit was exceeded for inclusion in the plugin
        report.

        Returns:
            ``str``: the message
        """
        if self.submission_metadata:
            return self._submission_allowed()[1]
