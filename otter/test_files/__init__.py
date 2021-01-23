"""
Classes for working with test files
"""

import math
import pprint
import pickle

from collections import namedtuple

# from .abstract_test import TestCollection
from .ok_test import OKTestFile

from ..check.logs import QuestionNotInLogException
from ..run.run_autograder.constants import DEFAULT_OPTIONS


GradingTestCaseResult = namedtuple(
    "GradingTestCaseResult", 
    ["name", "score", "possible", "hidden", "incorrect", "test_case_result"]
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
        test_files (``list`` of ``TestFile``): the test files passed to the constructor
        results (``dict``): maps test names to ``GradingTestCaseResult`` named tuples containing the 
            test result information
        output (``str``): a string to include in the output field for Gradescope
        all_hidden (``bool``): whether all results should be hidden from the student on Gradescope
        total (numeric): the total points earned by the submission
        possible (numeric): the total points possible based on the tests
        tests (``list`` of ``str``): list of test names according to the keys of ``results``
    """
    def __init__(self, test_files):
        self._plugin_data = {}
        self.test_files = test_files
        self.results = {}
        self.output = None
        self.all_hidden = False
        
        total_score, points_possible = 0, 0
        for test_file in test_files:
            # pts_per_case = test_file.value / len(test_file.test_case_results)
            case_pts = test_file.values
            for pts_per_case, test_case_result in zip(case_pts, test_file.test_case_results):
                name = test_case_result.test_case.name
                tr = GradingTestCaseResult(
                    name = test_case_result.test_case.name,
                    # the score is the number of points earned for the file divided by the number of tests in the file
                    # times 0 if the test case failed and 1 if it passed
                    score = pts_per_case * test_case_result.passed,
                    possible = pts_per_case,
                    # test_file = test_file,
                    hidden = test_case_result.test_case.hidden,
                    incorrect = not test_case_result.passed,
                    test_case_result = test_case_result
                )
                self.results[name] = tr

                total_score += pts_per_case * test_case_result.passed
                points_possible += pts_per_case
        
        self.total = total_score
        self.possible = points_possible
    
    def __repr__(self):
        return pprint.pformat(self.to_dict(), indent=2)

    @property
    def test_cases(self):
        """
        The names of all test cases tracked in these grading results
        """
        return list(self.results.keys())
    
    def get_result(self, test_name):
        """
        Returns the ``GradingTestCaseResult`` named tuple corresponding to the test with name ``test_name``

        Args:
            test_name (``str``): the name of the desired test
        
        Returns:
            ``GradingTestCaseResult``: the results of that test
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

    def update_result(self, test_name, **kwargs):
        """
        Updates the values in the ``GradingTestCaseResult`` object stored in ``self.results[test_name]`` 
        with the key-value pairs in ``kwargs``.

        Args:
            test_name (``str``): the name of the test
            kwargs: key-value pairs for updating the ``GradingTestCaseResult`` object
        """
        self.results[test_name] = self.results[test_name]._replace(**kwargs)

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
        for test_file in self.test_files:
            test_name = test_file.name
            # if ignore_hidden and self.get_results(test_name).hidden:
            #     continue
            
            # score = self.get_score(test_name)
            if ignore_hidden:
                tcrs = [test_case_result.passed for test_case_result in test_file.test_case_results if not test_case_result.hidden]
                score = sum(tcrs) / len(tcrs) * test_file.value
            else:
                score = test_file.grade * test_file.value
            try:
                result = log.get_results(test_name)
                # TODO fix
                logged_score = result.grade * result.value
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
        output = {}
        for test_name in self.test_cases:
            result = self.get_result(test_name)
            output[test_name] = dict(result._asdict())

        return output

    def to_gradescope_dict(self, config):
        """
        Converts these results into a dictionary formatted for Gradescope's autograder. Requires a 
        dictionary of configurations for the Gradescope assignment generated using Otter Generate.

        Args:
            config (``dict``): the grading configurations

        Returns:
            ``dict``: the results formatted for Gradescope
        """
        options = DEFAULT_OPTIONS.copy()
        options.update(config)

        output = {"tests": []}

        if self.output is not None:
            output["output"] = self.output

        # hidden visibility determined by show_hidden_tests_on_release
        hidden_test_visibility = ("hidden", "after_published")[options["show_hidden"]]
        # no_separate_visibility = options["test_visibility"]
        # assert no_separate_visibility in ["hidden", "visible", "after_published"]

        for test_name in self.test_cases:
            result = self.get_result(test_name)
            hidden, incorrect = result.hidden, result.incorrect
            score, possible = result.score, result.possible
            # public_score, hidden_score = score * options["public_multiplier"], score * (1 - options["public_multiplier"])
            # public_possible, hidden_possible = possible * options["public_multiplier"], possible * (1 - options["public_multiplier"])

            output["tests"].append({
                "name": result.name,
                "score": score,
                "max_score": possible,
                "visibility": hidden_test_visibility if hidden else 'visible',
                "output": result.test_case_result.message
            })

        if options["show_stdout"]:
            output["stdout_visibility"] = "after_published"

        if options["points_possible"] is not None:
            # output["score"] = self.total / self.possible * options["points_possible"]
            try:
                output["score"] = self.total / self.possible * options["points_possible"]
            except ZeroDivisionError:
                output["score"] = 0

        if options["score_threshold"] is not None:
            try:
                if self.total / self.possible >= config["score_threshold"]:
                    output["score"] = options["points_possible"] or self.possible
                else:
                    output["score"] = 0
            except ZeroDivisionError:
                if 0 >= config["score_threshold"]:
                    output["score"] = options["points_possible"] or self.possible
                else:
                    output["score"] = 0

        if self.all_hidden:
            for test in output["tests"]:
                test["visibility"]  = "hidden"
            output["stdout_visibility"] = "hidden"
        
        return output
