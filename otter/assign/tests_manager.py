"""Assignment tests manager for Otter Assign"""

import os
import pprint
import re
import yaml

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .assignment import Assignment
from .constants import BEGIN_TEST_CONFIG_REGEX, END_TEST_CONFIG_REGEX, EXCEPTION_BASED_TEST_FILE_TEMPLATE
from .solutions import remove_ignored_lines
from .utils import get_source, str_to_doctest

from ..test_files.abstract_test import OK_FORMAT_VARNAME, TestFile
from ..test_files.metadata_test import NOTEBOOK_METADATA_KEY

# TODO: docstrings for this whole file

@dataclass
class TestCase:

    input: str

    output: str

    hidden: bool

    points: Union[int, float]

    success_message: Optional[str]

    failure_message: Optional[str]


class AssignmentTestsManager:

    assignment: Assignment

    _tests_by_question: Dict[str, List[TestCase]]

    _questions: Dict[str, Dict]

    def __init__(self, assignment):
        self.assignment = assignment
        self._tests_by_question = {}
        self._questions = {}

    def any_public_tests(self, question):
        """
        Returns whether any of the ``Test`` named tuples in ``test_cases`` are public tests.

        Args:
            test_cases (``list`` of ``Test``): list of test cases
        
        Returns:
            ``bool``: whether any of the tests are public
        """
        return any(not tc.hidden for tc in self._tests_by_question[question["name"]])

    def _add_test_case(self, question, test_case):
        question_name = question["name"]
        self._questions[question_name] = question

        if question_name not in self._tests_by_question:
            self._tests_by_question[question_name] = []

        self._tests_by_question[question_name].append(test_case)

    def _parse_test_config(self, source: List[str]):
        """
        """
        config, i = {}, None
        if re.match(BEGIN_TEST_CONFIG_REGEX, source[0], flags=re.IGNORECASE):
            for i, line in enumerate(source):
                if re.match(END_TEST_CONFIG_REGEX, line, flags=re.IGNORECASE):
                    break
            config = yaml.full_load("\n".join(source[1:i]))
            assert isinstance(config, dict), f"Invalid test config in cell {source}"

        return config, i

    def read_test(self, cell, question):
        """
        Returns the contents of a test as an ``(input, output, hidden, points, success_message, 
        failure_message)`` named tuple
        
        Args:
            cell (``nbformat.NotebookNode``): a test cell
            question (``dict``): question metadata

        Returns:
            ``Test``: test named tuple
        """
        source = get_source(cell)

        if source[0].lstrip().startswith("#"):
            hidden = bool(re.search(r"\bhidden\b", source[0], flags=re.IGNORECASE))
        else:
            hidden = False

        test_start_line = 0 if hidden else -1

        output = ''
        for o in cell['outputs']:
            output += ''.join(o.get('text', ''))
            results = o.get('data', {}).get('text/plain')
            if results and isinstance(results, list):
                output += results[0]
            elif results:
                output += results

        config, maybe_test_start_line = self._parse_test_config(source)
        test_start_line = maybe_test_start_line if maybe_test_start_line is not None else test_start_line

        hidden = config.get("hidden", hidden)
        points = config.get("points", None)
        success_message = config.get("success_message", None)
        failure_message = config.get("failure_message", None)

        test_source = "\n".join(remove_ignored_lines(get_source(cell)[test_start_line + 1:]))

        self._add_test_case(
            question,
            TestCase(test_source, output, hidden, points, success_message, failure_message),
        )

    def has_tests(self, question):
        return question.name in self._tests_by_question

    @staticmethod
    def _resolve_test_file_points(total_points, test_cases):
        TestFile.resolve_test_file_points(total_points, test_cases)
        return test_cases

    def _create_test_file_info(self, question_name):
        question = self._questions[question_name]
        test_cases = self._tests_by_question[question_name]

        points = question.points
        if isinstance(points, dict):
            points = points.get('each', 1) * len(test_cases)
        elif isinstance(points, list):
            if len(points) != len(test_cases):
                raise ValueError(
                    f"Error in question {question.name}: length of 'points' is {len(points)} "
                    f"but there are {len(test_cases)} tests")

        # check for errors in resolving points
        test_cases = self._resolve_test_file_points(points, test_cases)

        return {
            "name": question.name,
            "points": points,
            "test_cases": test_cases,
        }

    @staticmethod
    def _create_ok_test_case(test_case: TestCase):
        """
        Generates an OK test case for a test named tuple
        
        Args:
            test (``otter.assign.Test``): OK test for this test case

        Returns:
            ``dict``: the OK test case
        """
        code_lines = str_to_doctest(test_case.input.split('\n'), [])
        code_lines.append(test_case.output)

        ret = {
            'code': '\n'.join(code_lines),
            'hidden': test_case.hidden,
            'locked': False,
        }

        if test_case.points is not None:
            ret['points'] = test_case.points
        if test_case.success_message:
            ret['success_message'] = test_case.success_message
        if test_case.failure_message:
            ret['failure_message'] = test_case.failure_message

        return ret

    @classmethod
    def _create_ok_test_suite(cls, test_cases: List[TestCase]):
        """
        Generates an OK test suite for a list of tests as named tuples
        
        Args:
            tests (``list`` of ``otter.assign.Test``): test cases

        Returns:
            ``dict``: OK test suite
        """
        return  {
            'cases': [cls._create_ok_test_case(tc) for tc in test_cases],
            'scored': True,
            'setup': '',
            'teardown': '',
            'type': 'doctest'
        }

    def _format_test(self, name, points, test_cases) -> Union[str, Dict[str, Any]]:
        """
        """
        if self.assignment.tests.ok_format:
            test = {
                "name": name,
                "points": points,
                "suites": [self._create_ok_test_suite(test_cases)],
            }

        else:
            template_kwargs = {
                "name": name, 
                "points": points, 
                "test_cases": test_cases, 
                "OK_FORMAT_VARNAME": OK_FORMAT_VARNAME,
            }
            test = EXCEPTION_BASED_TEST_FILE_TEMPLATE.render(**template_kwargs)

        return test

    def write_tests(self, nb, test_dir, include_hidden=True, force_files=False):
        """
        """
        # TODO: move this notebook to the notebook metadata test classes
        if isinstance(nb, dict) and not self.assignment.tests.files:
            if NOTEBOOK_METADATA_KEY not in nb["metadata"]:
                nb["metadata"][NOTEBOOK_METADATA_KEY] = {}
            nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"] = {}
            nb["metadata"][NOTEBOOK_METADATA_KEY][OK_FORMAT_VARNAME] = \
                self.assignment.tests.ok_format

        test_ext = ".py" if self.assignment.is_python else ".R"
        for test_name in self._tests_by_question.keys():
            test_info = self._create_test_file_info(test_name)
            test_path = os.path.join(test_dir, test_name + test_ext)

            if not include_hidden:
                test_info["test_cases"] = [tc for tc in test_info["test_cases"] if not tc.hidden]

            test = \
                self._format_test(test_info["name"], test_info["points"], test_info["test_cases"])

            if self.assignment.tests.files or force_files:
                with open(test_path, "w+") as f:
                    if isinstance(test, dict):
                        f.write(f"{OK_FORMAT_VARNAME} = True\n\ntest = ")
                        pprint.pprint(test, f, indent=4, width=200, depth=None)

                    else:
                        f.write(test)

            else:
                # TODO: move this notebook to the notebook metadata test classes
                nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"][test_info["name"]] = test

    def determine_question_point_value(self, question):
        """
        Determine the point value of a question using the question metadata and list of test cases.

        Args:
            question_metadata (``dict[str, object]``): the question metadata
            test_cases (``list[Test]``): the test cases for the question; if a manual question, this
                list should be empty

        Returns:
            number: the point value of the question
        """
        test_cases = self._tests_by_question.get(question.name, [])
        if len(test_cases) == 0:
            if question.points is None and question.manual:
                raise ValueError(
                    f"Point value unspecified for question with no test cases: {question.name}")

            return question.points if question.points is not None else 1

        resolved_test_cases = TestFile.resolve_test_file_points(question.points, test_cases)
        points = round(sum(tc.points for tc in resolved_test_cases), 5)
        return int(points) if points % 1 == 0 else points
