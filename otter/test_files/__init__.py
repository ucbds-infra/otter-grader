"""Classes for working with test files and test results"""

import json
import math
import nbformat as nbf
import os
import pickle

from typing import Any, Optional, TYPE_CHECKING, TypeVar, Union

from .abstract_test import TestCase, TestCaseResult, TestFile
from .exception_test import ExceptionTestFile, test_case
from .metadata_test import NotebookMetadataExceptionTestFile, NotebookMetadataOKTestFile
from .ok_test import OKTestFile
from .ottr_test import OttrTestFile
from ..nbmeta_config import NBMetadataConfig, OK_FORMAT_VARNAME
from ..utils import format_exception, QuestionNotInLogException


__all__ = [
    "create_test_file",
    "GradingResults",
    "test_case",
    "TestCase",
    "TestFile",
]


T = TypeVar("T")


def create_test_file(
    path: str,
    nbmeta_config: NBMetadataConfig,
    test_name: Optional[str] = None,
) -> TestFile:
    """
    Read a test file or a notebook file and determine the correct ``TestFile`` subclass for this test.

    If ``path`` is not a notebook, the file is executed as a Python script and a global variable is
    used to determine whether the test is OK-formatted or not.

    Args:
        path (``str``): the path to the test file or notebook
        test_name (``str``): the name of the test in the notebook metadata, if ``path`` is
            the path to a Jupyter notebook

    Returns:
        ``TestFile``: an instance of the correct test file

    Raises:
        ``ValueError``: if there is no test name specified and ``path`` is a notebook file
        ``RuntimeError``: if the test file does not define the ``OK_FORMAT`` global variable
    """
    if os.path.splitext(path)[1] == ".ipynb":
        if test_name is None:
            raise ValueError("You must specify a test name when using notebook metadata tests")

        if nbmeta_config.ok_format:
            return NotebookMetadataOKTestFile.from_nbmeta_config(path, nbmeta_config, test_name)

        else:
            return NotebookMetadataExceptionTestFile.from_nbmeta_config(
                path, nbmeta_config, test_name
            )

    env = {}
    with open(path) as f:
        exec(f.read(), env)

    if OK_FORMAT_VARNAME not in env:
        raise RuntimeError(
            f"Malformed test file: does not define the global variable '{OK_FORMAT_VARNAME}'"
        )

    if env[OK_FORMAT_VARNAME]:
        return OKTestFile.from_file(path)

    else:
        return ExceptionTestFile.from_file(path)


class GradingResults:
    """
    Stores and wrangles test result objects

    Initialize with a list of ``otter.test_files.abstract_test.TestFile`` subclass objects and
    this class will store the results as named tuples so that they can be accessed/manipulated easily.
    Also contains methods to put the results into a nice ``dict`` format or into the correct format
    for Gradescope.

    Args:
        results (``list[TestFile]``): the list of test file objects summarized in this grade
    """

    results: dict[str, TestFile]
    """maps test/question names to their ``TestFile`` objects (which store the results)"""

    output: Optional[str]
    """a string to include in the output field for Gradescope"""

    all_hidden: bool
    """whether all results should be hidden from the student on Gradescope"""

    pdf_error: Optional[Exception]
    """
    an error thrown while generating/submitting a PDF of the submission to display to students in
    the Gradescope results
    """

    notebook: Optional[nbf.NotebookNode]
    """the executed notebook with outputs that gave these results"""

    _plugin_data: dict[str, Any]
    """data requested to be stored in the results by plugins"""

    file: Optional[str] = None
    """the submission file that generated these results; not populated by default"""

    _catastrophic_error: Optional[Exception]
    """an error that prevented grading from completing"""

    def __init__(self, test_files: list[TestFile], notebook: Optional[nbf.NotebookNode] = None):
        self.results = {tf.name: tf for tf in test_files}
        self.output = None
        self.all_hidden = False
        self.pdf_error = None
        self.notebook = notebook
        self._catastrophic_error = None
        self._plugin_data = {}

    def __repr__(self):
        return self.summary()

    @classmethod
    def from_ottr_json(cls, ottr_output: dict[str, Any]) -> "GradingResults":
        """
        Creates a ``GradingResults`` object from the JSON output of Ottr (Otter's R client).

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
                test_cases.append(
                    TestCase(
                        name=tc["name"],
                        body=tc["code"],
                        hidden=tc["hidden"],
                        points=tc["points"],
                        success_message=tc["success_message"],
                        failure_message=tc["failure_message"],
                    )
                )
                test_case_results.append(
                    TestCaseResult(
                        test_case=test_cases[-1],
                        message=tcr["error"],
                        passed=tcr["passed"],
                    )
                )

            # fix the point values in each test case
            test_cases = TestFile.resolve_test_file_points(tfr.get("points"), test_cases)

            # TestFile.resolve_test_file_points returns a copy of each TestCase, so update the
            # TestCaseResults
            for tc, tcr in zip(test_cases, test_case_results):
                tcr.test_case = tc

            test_file = OttrTestFile(
                name=os.path.splitext(os.path.basename(tfr["filename"]))[0],
                path=tfr["filename"],
                test_cases=test_cases,
            )
            test_file.test_case_results = test_case_results

            test_files.append(test_file)

        return cls(test_files)

    @classmethod
    def without_results(cls, e: Exception) -> "GradingResults":
        """
        Creates an empty results object that represents an execution failure during autograding.

        The returned results object will alert students and instructors to this failure, providing
        the error message and traceback to instructors, and report a score of 0 on Gradescope.

        Args:
            e (``Exception``): the error that was thrown

        Returns:
            ``GradingResults``: the results object
        """
        instc = cls([])
        instc._catastrophic_error = e
        return instc

    @property
    def test_files(self) -> list[str]:
        """the names of all test files tracked in these grading results"""
        return list(self.results.keys())

    @property
    def total(self) -> Union[int, float]:
        """the total points earned"""
        if self._catastrophic_error:
            return 0
        return sum(tr.score for tr in self.results.values())

    @property
    def possible(self) -> Union[int, float]:
        """the total points possible"""
        if self._catastrophic_error:
            return 0
        return sum(tr.possible for tr in self.results.values())

    @property
    def percent(self) -> float:
        """the ratio of points earned, rounded to 4 digits"""
        if self.possible == 0:
            return 0
        return round(self.total / self.possible, 4)

    @property
    def passed_all_public(self) -> bool:
        """whether all public tests in these results passed"""
        return all(tr.passed_all_public for tr in self.results.values())

    @property
    def catastrophic_error(self) -> Optional[Exception]:
        """an error that prevented grading from completing, if applicable"""
        return self._catastrophic_error

    def get_result(self, test_name: str) -> TestFile:
        """
        Returns the ``TestFile`` corresponding to the test with name ``test_name``

        Args:
            test_name (``str``): the name of the desired test

        Returns:
            ``TestFile``: the graded test file object
        """
        return self.results[test_name]

    def get_score(self, test_name: str) -> Union[int, float]:
        """
        Returns the score of a test tracked by these results

        Args:
            test_name (``str``): the name of the test

        Returns:
            ``int | float``: the score
        """
        result = self.results[test_name]
        return result.score

    def update_score(self, test_name: str, new_score: Union[int, float]):
        """
        Override the score for the specified test file.

        Args:
            test_name (``str``): the name of the test file
            new_score (``int | float``): the new score
        """
        self.results[test_name].update_score(new_score)

    def set_output(self, output: str):
        """
        Updates the ``output`` field of the results JSON with text relevant to the entire submission.
        See https://gradescope-autograders.readthedocs.io/en/latest/specs/ for more information.

        Args:
            output (``str``): the output text
        """
        self.output = output

    def clear_results(self):
        """
        Empties the dictionary of results.
        """
        self.results = {}

    def hide_everything(self):
        """
        Indicates that all results should be hidden from students on Gradescope.
        """
        self.all_hidden = True

    def set_plugin_data(self, plugin_name: str, data: Any):
        """
        Stores plugin data for plugin ``plugin_name`` in the results. ``data`` must be picklable.

        Args:
            plugin_name (``str``): the importable name of a plugin
            data (any): the data to store; must be serializable with ``pickle``
        """
        try:
            pickle.dumps(data)
        except:
            raise ValueError(f"Data was not picklable: {data}")
        self._plugin_data[plugin_name] = data

    def get_plugin_data(self, plugin_name: str, default: Optional[T] = None) -> T:
        """
        Retrieves data for plugin ``plugin_name`` in the results.

        This method uses ``dict.get`` to retrieve the data, so a ``KeyError`` is never raised if
        ``plugin_name`` is not found; rather, it returns ``None``.

        Args:
            plugin_name (``str``): the importable name of a plugin
            default (any): a default value to return if ``plugin_name`` is not found

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

    def verify_against_log(self, log: "Log", ignore_hidden: bool = True) -> list[str]:
        """
        Verifies these scores against the results stored in this log using the results returned by
        ``Log.get_results`` for comparison. A discrepancy occurs if the scores differ by more than
        the default tolerance of ``math.isclose``. If ``ignore_hidden`` is ``True``, hidden tests
        are ignored when verifying scores.

        Args:
            log (``otter.check.logs.Log``): the log to verify against
            ignore_hidden (``bool``): whether to ignore hidden tests during verification

        Returns:
            ``list[str]``: a list of error messages for discrepancies; if none were found, the list
                is empty
        """
        l = []
        for test_name, test_file in self.results.items():
            if ignore_hidden:
                tcrs = [
                    test_case_result
                    for test_case_result in test_file.test_case_results
                    if not test_case_result.test_case.hidden
                ]
                score = sum(tcr.test_case.points for tcr in tcrs if tcr.passed)
            else:
                score = test_file.score
            try:
                tf = log.get_results(test_name)
                if not isinstance(tf, TestFile):
                    l.append(f"No score logged for {test_name}")
                    continue
                if not math.isclose(score, tf.score):
                    l.append(
                        f"Score for {test_name} ({score:.3f}) differs from logged score "
                        f"({tf.score:.3f})"
                    )
            except QuestionNotInLogException:
                l.append(f"No score for {test_name} found in this log")
        return l

    def to_report_str(self) -> str:
        """
        Returns these results as a report string generated using the ``__repr__`` of the
        ``TestFile`` class.

        Returns:
            ``str``: the report
        """
        return "\n".join(repr(test_file) for test_file in self.test_files)

    def to_dict(self) -> dict[str, Any]:
        """
        Converts these results into a dictionary, extending the fields of the named tuples in
        ``results`` into key, value pairs in a ``dict``.

        Returns:
            ``dict``: the results in dictionary form
        """
        return {tn: tf.to_dict() for tn, tf in self.results.items()}

    def summary(self, public_only: bool = False) -> str:
        """
        Generate a summary of these results and return it as a string.

        Args:
            public_only (``bool``): whether only public test cases should be included

        Returns:
            ``str``: the summary of results
        """
        if self._catastrophic_error:
            return str(self._catastrophic_error)
        return "\n\n".join(tf.summary(public_only=public_only) for _, tf in self.results.items())

    def has_catastrophic_failure(self) -> bool:
        """
        Returns whether these results contain a catastrophic error (i.e. an error that prevented
        submission results from being generated or read).

        Returns:
            ``bool``: whether there is such an error
        """
        return self._catastrophic_error is not None

    def to_gradescope_dict(self, ag_config: "AutograderConfig") -> dict[str, Any]:
        """
        Convert these results into a dictionary formatted for Gradescope's autograder.

        Args:
            ag_config (``otter.run.run_autograder.autograder_config.AutograderConfig``): the
                autograder config

        Returns:
            ``dict``: the results formatted for Gradescope
        """
        output = {"tests": []}

        if self._catastrophic_error:
            output["tests"].append(
                {
                    "name": "Autograder Failed",
                    "visibility": "visible",
                    "output": "The autograder failed to produce any results. Please alert your instructor to this failure for assistance in debugging it.",
                    "status": "failed",
                }
            )
            tb = format_exception(self._catastrophic_error)
            output["tests"].append(
                {
                    "name": "Autograder Exception",
                    "visibility": "hidden",
                    "output": f"The exception below was thrown when attempting to read the results from executing the notebook. (This message is not visible to students.)\n\n{tb}",
                    "status": "failed",
                }
            )
            output["score"] = 0
            return output

        if self.output is not None:
            output["output"] = self.output

        # hidden visibility determined by show_hidden
        hidden_test_visibility = ("hidden", "after_published")[ag_config.show_hidden]

        # if show_all_public is true and all tests are public tests, display all tests in results
        if ag_config.show_all_public and all(tf.all_public for tf in self.results.values()):
            hidden_test_visibility = "visible"

        # start w/ summary of public tests
        if not ag_config.show_hidden or ag_config.force_public_test_summary:
            output["tests"].append(
                {
                    "name": "Public Tests",
                    "visibility": "visible",
                    "output": self.summary(public_only=True),
                    "status": "passed" if self.passed_all_public else "failed",
                }
            )

        # add PDF error test if indicated
        if ag_config.warn_missing_pdf and self.pdf_error is not None:
            output["tests"].append(
                {
                    "name": "PDF Generation Failed",
                    "visibility": "visible",
                    "output": str(self.pdf_error),
                    "status": "failed",
                }
            )

        for test_name in self.test_files:
            test_file = self.get_result(test_name)
            score, possible = test_file.score, test_file.possible

            output["tests"].append(
                {
                    "name": test_file.name,
                    "score": round(score, 5),
                    "max_score": round(possible, 5),
                    "visibility": hidden_test_visibility,
                    "output": test_file.summary(),
                }
            )

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
                test["visibility"] = "hidden"
            output["stdout_visibility"] = "hidden"

        return output


if TYPE_CHECKING:
    from ..check.logs import Log
    from ..run import AutograderConfig
