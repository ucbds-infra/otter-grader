"""Abstract test objects for providing a schema to write and parse test cases"""

import random

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, replace
from textwrap import indent
from typing import List, Optional, Union


@dataclass
class TestCase:
    """
    A dataclass representing a single test case in a test file.
    """

    name: str
    """the name of the test case"""

    body: str
    """the code for the test case"""

    hidden: bool
    """whether this test case is hidden from students"""

    points: Optional[Union[int, float]]
    """the point value of this test case"""

    success_message: Optional[str]
    """a message to show to students if this test cases passes"""

    failure_message: Optional[str]
    """a message to show to students if this test cases fails"""


@dataclass
class TestCaseResult:
    """
    A dataclass representing the results of running a test case.
    """

    test_case: TestCase
    """the test case"""

    message: Optional[str]
    """an error message if the test case failed"""

    passed: bool
    """whether the test case was passed"""


class TestFile(ABC):
    """
    An (abstract) single test file for Otter. This ABC defines how test results are represented and
    sets up the instance variables tracked by tests. Subclasses should implement the abstract class
    method ``from_file`` and the abstract instance method ``run``.

    Args:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list[TestCase]``): a list of parsed tests to be run
        all_or_nothing (``bool``): whether the test should be graded all-or-nothing across cases
    """

    name: str
    """the name of test file"""

    path: str
    """the path to the test file"""

    test_cases: List[TestCase]
    """a list of parsed tests to be run"""

    all_or_nothing: bool
    """whether the test should be graded all-or-nothing across cases"""

    test_case_results: List[TestCaseResult]
    """a list of results for the test cases in ``test_cases``"""

    _score: Optional[Union[int, float]]
    """an override for the overall score for this test file"""

    def _repr_html_(self):
        if self.passed_all:
            all_passed_emoji = random.choice(['🍀', '🎉', '🌈', '🙌', '🚀', '🌟', '✨', '💯'])
            if any(tcr.test_case.success_message is not None for tcr in self.test_case_results):
                ret = f"<p><strong><pre style='display: inline;'>{self.name}</pre></strong> passed! {all_passed_emoji}</p>"
                for tcr in self.test_case_results:
                    if tcr.test_case.success_message is not None:
                        ret += f"<p><strong><pre style='display: inline;'>{tcr.test_case.name}</pre> message:</strong> {tcr.test_case.success_message}</p>"
                return ret
            return f"<p><strong><pre style='display: inline;'>{self.name}</pre></strong> passed! {all_passed_emoji}</p>"
        else:
            ret = f"<p><strong style='color: red;'><pre style='display: inline;'>{self.name}</pre> results:</strong></p>"
            for tcr in self.test_case_results:
                if tcr.passed and tcr.test_case.success_message is not None:
                    ret += f"<p><strong><pre style='display: inline;'>{tcr.test_case.name}</pre> message:</strong> {tcr.test_case.success_message}</p>"
                if not tcr.passed and tcr.test_case.failure_message is not None:
                    ret += f"<p><strong><pre style='display: inline;'>{tcr.test_case.name}</pre> message:</strong> {tcr.test_case.failure_message}</p>"
                ret += f"<p><strong><pre style='display: inline;'>{tcr.test_case.name}</pre> result:</strong></p>"
                ret += f"<pre>{indent(tcr.message, '    ')}</pre>"

            return ret

    def __repr__(self):
        return self.summary()

    def __init__(self, name, path, test_cases, all_or_nothing=True):
        self.name = name
        self.path = path
        self.test_cases = test_cases
        self.all_or_nothing = all_or_nothing
        self.test_case_results = []
        self._score = None

    @staticmethod
    def resolve_test_file_points(total_points, test_cases):
        if isinstance(total_points, list):
            if len(total_points) != len(test_cases):
                raise ValueError("Points specified in test has different length than number of test cases")
            test_cases = [replace(tc, points=pt) for tc, pt in zip(test_cases, total_points)]
            total_points = None

        elif total_points is not None and not isinstance(total_points, (int, float)):
            raise TypeError(f"Test spec points has invalid type: {total_points}")

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
                raise ValueError(f"More points specified in test cases than allowed for test")

            else:
                try:
                    per_remaining = (total_points - pre_specified) / sum(1 for p in point_values if p is None)
                except ZeroDivisionError:
                    per_remaining = 0.0

        else:
            if pre_specified == 0 and all(p in (0, None) for p in point_values):
                # if only zeros specified, assume test worth 1 pt and divide amongst nonzero cases
                try:
                    per_remaining = 1 / sum(p is None for p in point_values)
                except ZeroDivisionError:
                    per_remaining = 0.0

            elif pre_specified == 0:
                per_remaining = 1 / len(point_values)

            else:
                # assume all other tests are worth 0 points
                per_remaining = 0.0

        point_values = [p if p is not None else per_remaining for p in point_values]
        return [replace(tc, points=p) for tc, p in zip(test_cases, point_values)]

    @property
    def passed_all(self):
        return all(tcr.passed for tcr in self.test_case_results)

    @property
    def passed_all_public(self):
        return all(tcr.passed for tcr in self.test_case_results if not tcr.test_case.hidden)

    @property
    def all_public(self):
        return all(not tc.hidden for tc in self.test_cases)

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
            "test_cases": [asdict(tc) for tc in self.test_cases],
            "all_or_nothing": self.all_or_nothing,
            "test_case_results": [asdict(tcr) for tcr in self.test_case_results],
        }

    def summary(self, public_only=False):
        if (not public_only and self.passed_all) or (public_only and self.passed_all_public):
            ret = f"{self.name} results: All test cases passed!"
            if (not public_only and self.passed_all) and \
                    any(tcr.test_case.success_message is not None for tcr in self.test_case_results):
                for tcr in self.test_case_results:
                    if tcr.test_case.success_message is not None:
                        ret += f"\n{tcr.test_case.name} message: {tcr.test_case.success_message}"
            return ret

        tcrs = self.test_case_results
        if public_only:
            tcrs = [tcr for tcr in tcrs if not tcr.test_case.hidden]

        tcr_summaries = []
        for tcr in tcrs:
            smry = ""
            if tcr.passed and tcr.test_case.success_message is not None:
                smry += f"{tcr.test_case.name} message: {tcr.test_case.success_message}\n\n"
            if not tcr.passed and tcr.test_case.failure_message is not None:
                smry += f"{tcr.test_case.name} message: {tcr.test_case.failure_message}\n\n"
            smry += f"{tcr.test_case.name} result:\n"
            smry += f"{indent(tcr.message.strip(), '    ')}\n\n"

            tcr_summaries.append(smry.strip())

        return f"{self.name} results:\n" + indent("\n\n".join(tcr_summaries), "    ")

    @classmethod
    @abstractmethod
    def from_file(cls, path):
        ...

    @abstractmethod
    def run(self, global_environment):
        ...
