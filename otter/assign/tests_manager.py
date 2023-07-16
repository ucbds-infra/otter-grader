"""Assignment tests manager for Otter Assign"""

import os
import pandas as pd
import pprint
import re
import yaml

from dataclasses import dataclass
from jinja2 import Template
from typing import Any, Dict, List, Optional, Union

from .assignment import Assignment
from .question_config import QuestionConfig
from .solutions import remove_ignored_lines
from .utils import get_source, str_to_doctest

from ..test_files.abstract_test import OK_FORMAT_VARNAME, TestFile
from ..utils import NOTEBOOK_METADATA_KEY


BEGIN_TEST_CONFIG_REGEX = r'(?:.\s*=\s*)?""?"?\s*#\s*BEGIN\s*TEST\s*CONFIG'
END_TEST_CONFIG_REGEX = r'""?"?\s*#\s*END\s*TEST\s*CONFIG'

EXCEPTION_BASED_TEST_FILE_TEMPLATE = Template("""\
from otter.test_files import test_case

{{ OK_FORMAT_VARNAME }} = False

name = "{{ name }}"
points = {{ points }}

{% for tc in test_cases %}@test_case(points={{ tc.points }}, hidden={{ tc.hidden }}{% if tc.success_message is not none %}, 
    success_message="{{ tc.success_message }}"{% endif %}{% if tc.failure_message is not none %}, 
    failure_message="{{ tc.failure_message }}"{% endif %})
{{ tc.input }}
{% endfor %}
""")


@dataclass
class TestCase:
    """
    A dataclass representing a test case for a question.
    """

    input: str
    """the input of the test case"""

    output: str
    """the expected output of the test case"""

    hidden: bool
    """whether the test case is hidden"""

    points: Optional[Union[int, float]]
    """the point value of the test case"""

    success_message: Optional[str]
    """a message to show to the student if the test passes"""

    failure_message: Optional[str]
    """a message to show to the student if the test fails"""


class AssignmentTestsManager:
    """
    A class for creating and managing test cases for an assignment.

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment config
    """

    assignment: Assignment
    """the assignment config"""

    _tests_by_question: Dict[str, List[TestCase]]
    """a dictionary mapping question names to lists of test cases"""

    _questions: Dict[str, QuestionConfig]
    """a dictionary mapping question names to ``QuestionConfig`` objects"""

    def __init__(self, assignment):
        self.assignment = assignment
        self._tests_by_question = {}
        self._questions = {}

    def any_public_tests(self, question):
        """
        Determine whether any of the test cases in the specified question are public.

        Args:
            question (``otter.assign.question_config.QuestionConfig``): the question config

        Returns:
            ``bool``: whether any of the test cases for the question are public
        """
        return any(not tc.hidden for tc in self._tests_by_question[question["name"]])

    def _add_test_case(self, question, test_case):
        """
        Track a test case for the specified question.

        Args:
            question (``otter.assign.question_config.QuestionConfig``): the question config
            test_case (``TestCase``): the test case to track
        """
        question_name = question["name"]
        self._questions[question_name] = question

        if question_name not in self._tests_by_question:
            self._tests_by_question[question_name] = []

        self._tests_by_question[question_name].append(test_case)

    def _parse_test_config(self, source: List[str]):
        """
        Parse test configurations from the test cell source.

        Args:
            source (``list[str]``): the source lines of the test cell

        Returns:
            ``tuple[dict, int | None]``: the parsed config and the index in ``source`` of the line
                at which the config ended, if any
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
        Parse and track a test case from the provided cell for the specified question.

        Args:
            cell (``nbformat.NotebookNode``): a test cell
            question (``otter.assign.question_config.QuestionConfig``): the question config
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
        """
        Determine whether the specified question has any test cases.

        Args:
            question (``otter.assign.question_config.QuestionConfig``): the question config

        Returns:
            ``bool``: whether the question has any test cases
        """
        return question.name in self._tests_by_question

    @staticmethod
    def _resolve_test_file_points(total_points, test_cases):
        """
        Validate and reformat the point values of the provided test cases taking into account the
        total points for the question.

        For Python, this is validation doesn't change the underlying test cases and only raises an
        error if the specified point values are invalid. This may not be the case for other
        languages, however.

        Args:
            total_points (``int | float | list[int | float | None] | None``): the value of the
                ``points`` configuration for the question
            test_cases (``list[TestCase]``): the test cases for the question

        Returns:
            ``list[TestCase]``: updated test cases
        """
        TestFile.resolve_test_file_points(total_points, test_cases)
        return test_cases

    def _create_test_file_info(self, question_name):
        """
        Create a ``dict`` containing the test file information for the question with the specified
        name.

        Args:
            question_name (``str``): the question name

        Returns:
            ``dict``: the test file info
        """
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
        Create an OK-formatted test case for a test case object.

        Args:
            test (``TestCase``): the test case to convert to OK format

        Returns:
            ``dict``: the OK-formatted test case
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
        Create an OK-formatted test suite for a list of test cases.

        Args:
            test_cases (``list[TestCase]``): the test cases

        Returns:
            ``dict``: the OK-formatted test suite
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
        Format the test cases for a question based on the assignment config.

        Args:
            name (``str``): the name of the question
            points (``int | float | list[int | float | None] | None``): the ``points`` configuration
                from the question config
            test_cases (``list[TestCase]``): the test cases for the question

        Returns:
            ``dict | str``: the formatted test file
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
        Write all test files to a notebook's metadata or a tests directory.

        Args:
            nb (``nbformat.NotebookNode``): the notebook
            test_dir (``pathlib.Path | str``): the tests directory
            include_hidden (``bool``): whether to include hidden test cases
            force_files (``bool``): whether to force writing to test files (overriding the
                assignment config)
        """
        # TODO: move this notebook to the notebook metadata test classes
        if isinstance(nb, dict) and not self.assignment.tests.files and not force_files:
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
                if isinstance(test_info["points"], list):
                    test_info["points"] = [p for tc, p in \
                        zip(test_info["test_cases"], test_info["points"]) if not tc.hidden]

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
        Determine the point value of a question using the question config and its test cases.

        Args:
            question (``otter.assign.question_config.QuestionConfig``): the question config

        Returns:
            ``int | float``: the point value of the question
        """
        test_cases = self._tests_by_question.get(question.name, [])

        points = question.points
        if isinstance(points, dict):
            points = points.get('each', 1) * len(test_cases)

        if len(test_cases) == 0:
            if points is None and question.manual:
                raise ValueError(
                    f"Point value unspecified for question with no test cases: {question.name}")

            return points if points is not None else 1

        try:
            resolved_test_cases = TestFile.resolve_test_file_points(points, test_cases)
        except Exception as e:
            raise type(e)(f"Error in \"{question.name}\" test cases: {e}")

        points = round(sum(tc.points for tc in resolved_test_cases), 5)
        return int(points) if points % 1 == 0 else points

    def generate_assignment_summary(self):
        """
        Generate a summary of the assignment's questions.

        Returns:
            ``str``: the summary
        """
        rows, manual, autograded, total = [], 0, 0, 0
        for question_name in sorted(self._tests_by_question.keys()):
            config = self._questions[question_name]
            points = self.determine_question_point_value(config)
            rows.append({"name": question_name, "points": points})
            total += points
            if config.manual: manual += points
            else: autograded += points

        summary = f"Assignment summary:\n"
        summary += f"Total points: {total}\n"
        summary += f"Autograded:   {autograded}\n"
        summary += f"Manual:       {manual}\n\n"
        summary += str(pd.DataFrame(rows))
        return summary
