"""Tests for ``otter.test_files.GradingResults``"""

import traceback

from otter.run.run_autograder.autograder_config import AutograderConfig
from otter.test_files import GradingResults


class TestGradingResults:
    """
    Tests for ``otter.test_files.GradingResults``.
    """

    def test_without_results(self):
        """
        Tests for ``otter.test_files.GradingResults.wtihout_results``.
        """
        def foo():
            raise Exception("nope")

        try:
            foo()
        except Exception as e:
            # this is a hacky way of ensuring that the exception has a traceback
            excp = e

        r = GradingResults.without_results(excp)

        tb = "".join(traceback.format_exception(type(excp), excp, excp.__traceback__))
        assert r.to_gradescope_dict(AutograderConfig()) == {
            "tests": [
                {
                    "name": "Autograder Failed", 
                    "visibility": "visible", 
                    "output": "The autograder failed to produce any results. Please alert your instructor to this failure for assistance in debugging it.",
                    "status": "failed",
                },
                {
                    "name": "Autograder Exception", 
                    "visibility": "hidden", 
                    "output": f"The exception below was thrown when attempting to read the results from executing the notebook. (This message is not visible to students.)\n\n{tb}", 
                    "status": "failed",
                },
            ],
            "score": 0,
        }
