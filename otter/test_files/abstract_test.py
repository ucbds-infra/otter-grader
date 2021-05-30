"""
Abstract base classes for working with test files and classes to represent collections of test and 
their results
"""

from abc import ABC, abstractmethod
from collections import namedtuple
from textwrap import dedent, indent
from typing import Tuple, List, Dict, Any
from jinja2 import Template
from pygments import highlight
from pygments.lexers import PythonConsoleLexer
from pygments.formatters import HtmlFormatter


# class for storing the test cases themselves
#   - body is the string that gets run for the test
#   - hidden is the visibility of the test case
#   - points is the number of points this test case is worth
TestCase = namedtuple("TestCase", ["name", "body", "hidden", "points"])


# class for storing the results of a single test _case_ (within a test file)
#   - message should be a string to print out to the student (ignored if passed is True)
#   - passed is whether the test case passed
#   - hidden is the visibility of the test case
TestCaseResult = namedtuple("TestCaseResult", ["test_case", "message", "passed"])


# TODO: fix reprs
class TestFile(ABC):
    """
    A (abstract) single test file for Otter. This ABC defines how test results are represented and sets
    up the instance variables tracked by tests. Subclasses should implement the abstract class method
    ``from_file`` and the abstract instance method ``run``.

    Args:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list`` of ``TestCase``): a list of parsed tests to be run
        all_or_nothing (``bool``, optional): whether the test should be graded all-or-nothing across
            cases

    Attributes:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list`` of ``TestCase``): a list of parsed tests to be run
        all_or_nothing (``bool``): whether the test should be graded all-or-nothing across
            cases
        test_case_results (``list`` of ``TestCaseResult``): a list of results for the test cases in
            ``test_cases``
    """

    def _repr_html_(self):
        if self.passed_all:
            return f"<p><strong><pre style='display: inline;'>{self.name}</pre></strong> passed!</p>"
        else:
            ret = f"<p><strong style='color: red;'><pre style='display: inline;'>{self.name}</pre> results:</strong></p>"
            for tcr in self.test_case_results:
                ret += f"<p><strong><pre style='display: inline;'>{tcr.test_case.name}</pre> result:</strong></p>"
                ret += f"<pre>{indent(tcr.message, '    ')}</pre>"
            return ret

    def __repr__(self):
        return self.summary()

    # @abstractmethod
    def __init__(self, name, path, test_cases, all_or_nothing=True):
        self.name = name
        self.path = path
        self.test_cases = test_cases
        self.all_or_nothing = all_or_nothing
        self.test_case_results = []
        self._score = None

    @staticmethod
    def resolve_test_file_points(total_points, test_cases):
        point_values = []
        for i, test_case in enumerate(test_cases):
            if test_case.points is not None:
                assert type(test_case.points) in (int, float), f"Invalid point type: {type(test_case.points)}"
                point_values.append(test_case.points)
            else:
                point_values.append(None)

        pre_specified = sum(p for p in point_values if p is not None)
        if total_points is not None:
            if pre_specified > total_points:
                raise ValueError(f"More points specified in test cases that allowed for test")
            else:
                per_remaining = (total_points - pre_specified) / sum(1 for p in point_values if p is None)
        else:
            # assume all other tests are worth 0 points
            if pre_specified == 0:
                per_remaining = 1 / len(point_values)
            else:
                per_remaining = 0.0

        point_values = [p if p is not None else per_remaining for p in point_values]
        return [tc._replace(points=p) for tc, p in zip(test_cases, point_values)]

    @property
    def passed_all(self):
        return all(tcr.passed for tcr in self.test_case_results)

    def passed_all_public(self):
        return all(tcr.passed for tcr in self.test_case_results if not tcr.test_case.hidden)

    @property
    def grade(self):
        if self.all_or_nothing and not self.passed_all:
            return 0
        elif self.all_or_nothing and self.passed_all:
            return 1
        else:
            return sum(tcr.test_case.points for tcr in self.test_case_results if tcr.passed) / \
                sum(tc.points for tc in self.test_cases)

    @property
    def score(self):
        if self._score is not None:
            return self._score
        return sum(tcr.test_case.points for tcr in self.test_case_results if tcr.passed)

    @property
    def possible(self):
        return sum(tc.points for tc in self.test_cases)

    def update_score(self, new_score):
        self._score = new_score

    def to_dict(self):
        return {
            "score": self.score,
            "possible": self.possible,
            "name": self.name,
            "path": self.path,
            "test_cases": [tc._asdict() for tc in self.test_cases],
            "all_or_nothing": self.all_or_nothing,
            "test_case_results": [tcr._asdict() for tcr in self.test_case_results],
        }

    def summary(self, public_only=False):
        if (not public_only and self.passed_all) or (public_only and self.passed_all_public):
            return f"{self.name} results: All test cases passed!"

        tcrs = self.test_case_results
        if public_only:
            tcrs = [tcr for tcr in tcrs if not tcr.test_case.hidden]
        
        tcr_summaries = []
        for tcr in tcrs:
            if not tcr.passed:
                tcr_summaries.append(tcr.message.strip())

        return f"{self.name} results:\n" + indent("\n".join(tcr_summaries), "    ")

    @classmethod
    @abstractmethod
    def from_file(cls, path):
        ...

    @abstractmethod
    def run(self, global_environment):
        ...
