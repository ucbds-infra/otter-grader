"""Support for OK-formatted test files"""

import doctest
import io
import os
import pathlib

from contextlib import redirect_stderr, redirect_stdout
from textwrap import dedent
from typing import Any

from .abstract_test import TestCase, TestCaseResult, TestFile
from ..utils import hide_outputs


def run_doctest(
    name: str, doctest_string: str, global_environment: dict[str, Any]
) -> tuple[bool, str]:
    """
    Run a single test with given ``global_environment``. Returns ``(True, '')`` if the doctest passes.
    Returns ``(False, failure_message)`` if the doctest fails.

    Args:
        name (``str``): name of doctest
        doctest_string (``str``): doctest in string form
        global_environment (``dict[str, Any]``): global environment resulting from the execution of
            a python script/notebook

    Returns:
        ``tuple[bool, str]``: results from running the test
    """
    examples = doctest.DocTestParser().parse(doctest_string, name)
    test = doctest.DocTest(
        [e for e in examples if isinstance(e, doctest.Example)],
        global_environment,
        name,
        None,
        None,
        doctest_string,
    )

    doctestrunner = doctest.DocTestRunner(verbose=True)

    runresults = io.StringIO()
    with redirect_stdout(runresults), redirect_stderr(runresults), hide_outputs():
        doctestrunner.run(test, clear_globs=False)
    with open(os.devnull, "w") as f, redirect_stderr(f), redirect_stdout(f):
        result = doctestrunner.summarize(verbose=True)
    # An individual test can only pass or fail
    if result.failed == 0:
        return (True, "")
    else:
        return False, runresults.getvalue()


class OKTestFile(TestFile):
    """
    A single OK-formatted test file for Otter.
    """

    def run(self, global_environment: dict[str, Any]):
        """
        Run the test cases on ``global_environment``, saving the results in
        ``self.test_case_results``.

        Arguments:
            ``global_environment`` (``dict``): result of executing a Python notebook/script
        """
        self.test_case_results = []
        for i, test_case in enumerate(self.test_cases):
            passed, result = run_doctest(
                self.name + " " + str(i), test_case.body, global_environment
            )
            if passed:
                result = "✅ Test case passed"
            else:
                result = "❌ Test case failed\n" + result

            self.test_case_results.append(
                TestCaseResult(
                    test_case=test_case,
                    message=result,
                    passed=passed,
                )
            )

    @classmethod
    def from_spec(cls, test_spec: dict[str, Any], path: str = "") -> "OKTestFile":
        """
        Parse an OK-formatted ``dict`` and return an ``OKTestFile``.

        Args:
            test_spec (``dict[str, Any]``): the OK-formatted ``dict``
            path (``str``): the path to the test file this ``dict`` was parsed from

        Returns:
            ``OKTestFile``: the new ``OKTestFile`` object created from the given file
        """
        # Make sure there is a name
        assert "name" in test_spec

        # Do not support multiple suites in the same file
        assert len(test_spec["suites"]) == 1

        test_suite = test_spec["suites"][0]

        # Only support doctest. I am unsure if other tests are implemented
        assert test_suite.get("type", "doctest") == "doctest"

        # Not setup and teardown supported
        assert not bool(test_suite.get("setup"))
        assert not bool(test_suite.get("teardown"))

        test_cases = []
        for i, test_case in enumerate(test_spec["suites"][0]["cases"]):
            test_cases.append(
                TestCase(
                    name=test_case.get("name", f"{test_spec['name']} - {i + 1}"),
                    body=dedent(test_case["code"]),
                    hidden=test_case.get("hidden", True),
                    points=test_case.get("points", None),
                    success_message=test_case.get("success_message", None),
                    failure_message=test_case.get("failure_message", None),
                )
            )

        # resolve point values for each test case
        spec_pts = test_spec.get("points", None)
        test_cases = cls.resolve_test_file_points(spec_pts, test_cases)

        # convert path into PurePosixPath for test name
        path = str(pathlib.Path(path).as_posix())

        # grab whether the tests are all-or-nothing
        all_or_nothing = test_spec.get("all_or_nothing", False)

        return cls(test_spec["name"], path, test_cases, all_or_nothing)

    @classmethod
    def from_metadata(cls, s: Any, path: str) -> "OKTestFile":
        """
        Parse an OK test file from its data stored in a notebook's metadata.

        Args:
            spec (``dict``): the test data from the notebook metadata
            path (``str``): the path to the notebook

        Returns:
            ``OKTestFile``: the parsed test file.
        """
        return cls.from_spec(s, path=path)

    @classmethod
    def from_file(cls, path: str) -> "OKTestFile":
        """
        Parse an OK-formatted test file and return an ``OKTestFile``.

        Args:
            path (``str``): the path to the test file

        Returns:
            ``OKTestFile``: the new ``OKTestFile`` object created from the given file
        """
        # ok test files are python files, with a global 'test' defined
        test_globals = {}
        with open(path) as f:
            exec(f.read(), test_globals)

        test_spec = test_globals["test"]

        return cls.from_spec(test_spec, path=path)
