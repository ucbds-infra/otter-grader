"""Classes for working with test files and test results"""

import json
import math
import nbformat
import os
import pickle

from collections import namedtuple

from .abstract_test import OK_FORMAT_VARNAME, TestCase, TestCaseResult, TestFile
from .exception_test import ExceptionTestFile, test_case
from .metadata_test import NotebookMetadataExceptionTestFile, NotebookMetadataOKTestFile
from .ok_test import OKTestFile
from .ottr_test import OttrTestFile

from ..check.logs import QuestionNotInLogException
from ..utils import NBFORMAT_VERSION, NOTEBOOK_METADATA_KEY


def create_test_file(path, test_name=None):
    """
    Read a test file or a notebook file and determine the correct ``TestFile`` subclass for this test.

    If ``path`` is not a notebook, the file is executed as a Python script and a global variable is
    used to determine whether the test is OK-formatted or not.

    Args:
        path (``str``): the path to the test file or notebook
        test_name (``str``, optional): the name of the test in the notebook metadata, if ``path`` is
            the path to a Jupyter notebook

    Returns:
        ``TestFile``: an instance of the correct test file
    """
    if os.path.splitext(path)[1] == ".ipynb":
        if test_name is None:
            raise ValueError("You must specify a test name when using notebook metadata tests")

        nb = nbformat.read(path, as_version=NBFORMAT_VERSION)
        if nb["metadata"][NOTEBOOK_METADATA_KEY][OK_FORMAT_VARNAME]:
            return NotebookMetadataOKTestFile.from_file(path, test_name)

        else:
            return NotebookMetadataExceptionTestFile.from_file(path, test_name)

    env = {}
    with open(path) as f:
        exec(f.read(), env)

    if OK_FORMAT_VARNAME not in env:
        raise RuntimeError(f"Malformed test file: does not define the global variable '{OK_FORMAT_VARNAME}'")

    if env[OK_FORMAT_VARNAME]:
        return OKTestFile.from_file(path)

    else:
        return ExceptionTestFile.from_file(path)


GradingTestCaseResult = namedtuple(
    "GradingTestCaseResult", 
    ["name", "score", "possible", "hidden", "incorrect", "test_case_result", "test_file"]
)


class GradingResults:
    """
    Stores and wrangles test result objects

    Initialize with a list of ``otter.test_files.abstract_test.TestFile`` subclass objects and 
    this class will store the results as named tuples so that they can be accessed/manipulated easily. 
    Also contains methods to put the results into a nice ``dict`` format or into the correct format 
    for Gradescope.

    Args:
        results (``list`` of ``TestFile``): the list of test file objects summarized in this grade

    Attributes:
        results (``dict``): maps test names to ``GradingTestCaseResult`` named tuples containing the 
            test result information
        output (``str``): a string to include in the output field for Gradescope
        all_hidden (``bool``): whether all results should be hidden from the student on Gradescope
        tests (``list`` of ``str``): list of test names according to the keys of ``results``
    """
    def __init__(self, test_files):
        self._plugin_data = {}
        self.results = {tf.name: tf for tf in test_files}
        # self.results = {}
        self.output = None
        self.all_hidden = False
        self.pdf_error = None

    def __repr__(self):
        return self.summary()

    @classmethod
    def from_ottr_json(cls, ottr_output):
        """
        Creates a ``GradingResults`` object from the JSON output of Ottr.

        Args:
            ottr_output (``str``): the JSON output of Ottr as a string

        Returns:
            ``GradingResults``: the Ottr grading results
        """
        test_file_results = json.loads(ottr_output)["test_file_results"]
        test_files = []
        for tfr in test_file_results:
            test_cases, test_case_results = [], []

            for tcr in tfr["test_case_results"]:
                tc = tcr["test_case"]
                test_cases.append(TestCase(
                    name = tc["name"],
                    body = tc["code"],
                    hidden = tc["hidden"],
                    points = tc["points"],
                    success_message = tc["success_message"],
                    failure_message = tc["failure_message"],
                ))
                test_case_results.append(TestCaseResult(
                    test_case = test_cases[-1],
                    message = tcr["error"],
                    passed = tcr["passed"],
                ))

            # fix the point values in each test case
            test_cases = TestFile.resolve_test_file_points(tfr.get("points"), test_cases)

            # TestFile.resolve_test_file_points returns a copy of each TestCase, so update the
            # TestCaseResults
            for tc, tcr in zip(test_cases, test_case_results):
                tcr.test_case = tc

            test_file = OttrTestFile(
                name = os.path.splitext(os.path.basename(tfr["filename"]))[0],
                path = tfr["filename"],
                test_cases = test_cases,
            )
            test_file.test_case_results = test_case_results

            test_files.append(test_file)

        return cls(test_files)

    @property
    def test_files(self):
        """
        ``list[TestFile]``: the names of all test files tracked in these grading results
        """
        return list(self.results.keys())

    @property
    def total(self):
        """
        ``int`` or ``float``: the total points earned
        """
        return sum(tr.score for tr in self.results.values())

    @property
    def possible(self):
        """
        ``int`` or ``float``: the total points possible
        """
        return sum(tr.possible for tr in self.results.values())

    @property
    def passed_all_public(self):
        """
        ``bool``: whether all public tests in these results passed
        """
        return all(tr.passed_all_public for tr in self.results.values())

    def get_result(self, test_name):
        """
        Returns the ``TestFile`` corresponding to the test with name ``test_name``

        Args:
            test_name (``str``): the name of the desired test

        Returns:
            ``TestFile``: the graded test file object
        """
        return self.results[test_name]

    def get_score(self, test_name):
        """
        Returns the score of a test tracked by these results

        Args:
            test_name (``str``): the name of the test

        Returns:
            ``int`` or ``float``: the score
        """
        result = self.results[test_name]
        return result.score

    def update_score(self, test_name, new_score):
        """
        Updates the values in the ``GradingTestCaseResult`` object stored in ``self.results[test_name]`` 
        with the key-value pairs in ``kwargs``.

        Args:
            test_name (``str``): the name of the test
            new_score (``int`` or ``float``): the new score
        """
        self.results[test_name].update_score(new_score)

    def set_output(self, output):
        """
        Updates the ``output`` field of the results JSON with text relevant to the entire submission.
        See https://gradescope-autograders.readthedocs.io/en/latest/specs/ for more information.

        Args:
            output (``str``): the output text
        """
        self.output = output

    def clear_results(self):
        """
        Empties the dictionary of results
        """
        self.results = {}

    def hide_everything(self):
        """
        Indicates that all results should be hidden from students on Gradescope
        """
        self.all_hidden = True

    def set_plugin_data(self, plugin_name, data):
        """
        Stores plugin data for plugin ``plugin_name`` in the results. ``data`` must be picklable.

        Args:
            plugin_name (``str``): the importable name of a plugin
            data (any): the data to store; must be serializable with ``pickle``
        """
        try:
            pickle.dumps(data)
        except:
            raise ValueError(f"Data was not pickleable: {data}")
        self._plugin_data[plugin_name] = data

    def get_plugin_data(self, plugin_name, default=None):
        """
        Retrieves data for plugin ``plugin_name`` in the results

        This method uses ``dict.get`` to retrive the data, so a ``KeyError`` is never raised if
        ``plugin_name`` is not found; rather, it returns ``None``.

        Args:
            plugin_name (``str``): the importable name of a plugin
            default (any, optional): a default value to return if ``plugin_name`` is not found

        Returns:
            any: the data stored for ``plugin_name`` if found
        """
        return self._plugin_data.get(plugin_name, default)

    def set_pdf_error(self, error: Exception):
        """
        Set a PDF generation error to be displayed as a failed (0-point) test on Gradescope.

        Args:
            error (``Exception``): the error thrown
        """
        self.pdf_error = error

    def verify_against_log(self, log, ignore_hidden=True):
        """
        Verifies these scores against the results stored in this log using the results returned by 
        ``Log.get_results`` for comparison. Prints a message if the scores differ by more than the 
        default tolerance of ``math.isclose``. If ``ignore_hidden`` is ``True``, hidden tests are
        ignored when verifying scores.

        Args:
            log (``otter.check.logs.Log``): the log to verify against
            ignore_hidden  (``bool``, optional): whether to ignore hidden tests during verification

        Returns:
            ``bool``: whether a discrepancy was found
        """
        found_discrepancy = False
        # for test_name in  self.test_cases:
        for test_name, test_file in self.results.items():
            if ignore_hidden:
                tcrs = [
                    test_case_result.passed
                    for test_case_result in test_file.test_case_results
                    if not test_case_result.test_case.hidden
                ]
                score = sum(tcr.test_case.points for tcr in tcrs)
            else:
                score = test_file.score
            try:
                result = log.get_results(test_name)
                # TODO fix
                logged_score = result.score
                if not math.isclose(score, logged_score):
                    print("Score for {} ({:.3f}) differs from logged score ({:.3f})".format(
                        test_name, score, logged_score
                    ))
                    found_discrepancy = True
            except QuestionNotInLogException:
                print(f"No score for {test_name} found in this log")
                found_discrepancy = True
        return found_discrepancy

    def to_report_str(self):
        """
        Returns these results as a report string generated using the ``__repr__`` of the ``TestFile``
        class.

        Returns:
            ``str``: the report
        """
        return "\n".join(repr(test_file) for test_file in self.test_files)

    def to_dict(self):
        """
        Converts these results into a dictinary, extending the fields of the named tuples in ``results``
        into key, value pairs in a ``dict``.

        Returns:
            ``dict``: the results in dictionary form
        """
        return {tn: tf.to_dict() for tn, tf in self.results.items()}

    def summary(self, public_only=False):
        """
        Generate a summary of these results and return it as a string.

        Args:
            public_only (``bool``, optional): whether only public test cases should be included

        Returns:
            ``str``: the summary of results
        """
        return "\n\n".join(tf.summary(public_only=public_only) for _, tf in self.results.items())

    def to_gradescope_dict(self, ag_config):
        """
        Converts these results into a dictionary formatted for Gradescope's autograder. Requires a 
        dictionary of configurations for the Gradescope assignment generated using Otter Generate.

        Args:
            ag_config (``otter.run.run_autograder.autograder_config.AutograderConfig``): the
                autograder config

        Returns:
            ``dict``: the results formatted for Gradescope
        """
        output = {"tests": []}

        if self.output is not None:
            output["output"] = self.output
            # TODO: use output to display public test case results?

        # hidden visibility determined by show_hidden
        hidden_test_visibility = ("hidden", "after_published")[ag_config.show_hidden]

        # if show_all_public is true and all tests are public tests, display all tests in results
        if ag_config.show_all_public and all(tf.all_public for tf in self.results.values()):
            hidden_test_visibility = "visible"

        # start w/ summary of public tests
        if not ag_config.show_hidden or ag_config.force_public_test_summary:
            output["tests"].append({
                "name": "Public Tests",
                "visibility": "visible",
                "output": self.summary(public_only=True),
                "status": "passed" if self.passed_all_public else "failed",
            })

        # add PDF error test if indicated
        if ag_config.warn_missing_pdf and self.pdf_error is not None:
            output["tests"].append({
                "name": "PDF Generation Failed",
                "visibility": "visible",
                "output": str(self.pdf_error),
                "status": "failed",
            })

        for test_name in self.test_files:
            test_file = self.get_result(test_name)
            score, possible = test_file.score, test_file.possible

            output["tests"].append({
                "name": test_file.name,
                "score": round(score, 5),
                "max_score": round(possible, 5),
                "visibility": hidden_test_visibility,
                "output": test_file.summary(),
            })

        if ag_config.show_stdout:
            output["stdout_visibility"] = "after_published"

        if ag_config.points_possible is not None:
            try:
                output["score"] = self.total / self.possible * ag_config.points_possible
            except ZeroDivisionError:
                output["score"] = 0

        if ag_config.score_threshold is not None:
            try:
                if self.total / self.possible >= ag_config.score_threshold:
                    output["score"] = ag_config.points_possible or self.possible
                else:
                    output["score"] = 0
            except ZeroDivisionError:
                if 0 >= ag_config.score_threshold:
                    output["score"] = ag_config.points_possible or self.possible
                else:
                    output["score"] = 0

        if self.all_hidden:
            for test in output["tests"]:
                test["visibility"]  = "hidden"
            output["stdout_visibility"] = "hidden"

        return output
