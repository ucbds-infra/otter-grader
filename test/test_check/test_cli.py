"""Tests for ``otter.check``"""

import contextlib
import os
import pytest

from glob import glob
from io import StringIO
from textwrap import dedent
from unittest import mock

from otter.check import main as check

from ..utils import TestFileManager


FILE_MANAGER = TestFileManager(__file__)


@pytest.fixture(autouse=True)
def cleanup_check_output(cleanup_enabled):
    yield
    if cleanup_enabled and os.path.exists(".OTTER_LOG"):
        os.remove(".OTTER_LOG")


def test_otter_check_script():
    """
    Checks that the script checker works
    """
    # run for each individual test
    for file in glob(FILE_MANAGER.get_path("tests/*.py")):
        # capture stdout
        output = StringIO()
        with contextlib.redirect_stdout(output):
            check(
                FILE_MANAGER.get_path("file0.py"),
                question = os.path.split(file)[1][:-3],
                tests_path = os.path.split(file)[0],
            )

        if os.path.split(file)[1] != "q2.py":
            assert output.getvalue().strip().split("\n")[-1].strip() == \
                "All tests passed!", \
                "Did not pass test at {}".format(file)

    # run the file for all questions
    output = StringIO()
    with contextlib.redirect_stdout(output):
        check(
            FILE_MANAGER.get_path("file0.py"), 
            tests_path = os.path.split(file)[0],
        )

    assert output.getvalue().strip() == \
        dedent("""\
            q1 results: All test cases passed!
            q2 results:
                q2 - 1 result:
                    ❌ Test case failed
                    Trying:
                        1 == 1
                    Expecting:
                        False
                    **********************************************************************
                    Line 2, in q2 0
                    Failed example:
                        1 == 1
                    Expected:
                        False
                    Got:
                        True

                q2 - 2 result:
                    ✅ Test case passed
            q3 results: All test cases passed!
            q4 results: All test cases passed!
            q5 results: All test cases passed!"""), \
        "Did not pass correct tests"


def test_otter_check_notebook():
    """
    Checks that the script checker works
    """
    # run for each individual test
    for file in glob(FILE_MANAGER.get_path("tests/*.py")):
        # capture stdout
        output = StringIO()
        with contextlib.redirect_stdout(output):
            check(
                FILE_MANAGER.get_path("test-nb.ipynb"), 
                question = os.path.split(file)[1][:-3],
                tests_path = os.path.split(file)[0],
            )

        if os.path.split(file)[1] != "q2.py":
            assert output.getvalue().strip().split("\n")[-1].strip() == \
                "All tests passed!", \
                "Did not pass test at {}".format(file)

    # run the file for all questions
    output = StringIO()
    with contextlib.redirect_stdout(output):
        check(
            FILE_MANAGER.get_path("test-nb.ipynb"), 
            tests_path = os.path.split(file)[0],
        )

    assert output.getvalue().strip() == \
        dedent("""\
            q1 results: All test cases passed!
            q2 results:
                q2 - 1 result:
                    ❌ Test case failed
                    Trying:
                        1 == 1
                    Expecting:
                        False
                    **********************************************************************
                    Line 2, in q2 0
                    Failed example:
                        1 == 1
                    Expected:
                        False
                    Got:
                        True

                q2 - 2 result:
                    ✅ Test case passed
            q3 results: All test cases passed!
            q4 results: All test cases passed!
            q5 results: All test cases passed!"""), \
        "Did not pass correct tests"
