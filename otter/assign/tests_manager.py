"""Assignment tests manager for Otter Assign"""

import ast
import nbformat as nbf
import os
import pandas as pd
import pathlib
import pprint
import re
import yaml

from jinja2 import Template
from typing import Any, Union

from .assignment import Assignment
from .question_config import QuestionConfig
from .utils import str_to_doctest
from ..nbmeta_config import NBMetadataConfig, OK_FORMAT_VARNAME
from ..test_files.abstract_test import TestCase, TestFile
from ..utils import get_source


BEGIN_TEST_CONFIG_REGEX = r'(?:.\s*=\s*)?""?"?\s*#\s*BEGIN\s*TEST\s*CONFIG'
END_TEST_CONFIG_REGEX = r'""?"?\s*#\s*END\s*TEST\s*CONFIG'

EXCEPTION_BASED_TEST_FILE_TEMPLATE = Template(
    """\
from otter.test_files import test_case

{{ OK_FORMAT_VARNAME }} = False

name = "{{ name }}"
points = {{ points }}{% if all_or_nothing %}
all_or_nothing = True{% endif %}

{% for tc in test_cases %}@test_case(points={{ tc.points }}, hidden={{ tc.hidden }}{% if tc.success_message is not none %}, 
    success_message="{{ tc.success_message }}"{% endif %}{% if tc.failure_message is not none %}, 
    failure_message="{{ tc.failure_message }}"{% endif %})
{{ tc.body }}

{% endfor %}
"""
)


class AssignmentTestsManager:
    """
    A class for creating and managing test cases for an assignment.

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment config
    """

    assignment: Assignment
    """the assignment config"""

    _tests_by_question: dict[str, list[TestCase]]
    """a dictionary mapping question names to lists of test cases"""

    _questions: dict[str, QuestionConfig]
    """a dictionary mapping question names to ``QuestionConfig`` objects"""

    def __init__(self, assignment: Assignment):
        self.assignment = assignment
        self._tests_by_question = {}
        self._questions = {}

    def any_public_tests(self, question: QuestionConfig) -> bool:
        """
        Determine whether any of the test cases in the specified question are public.

        Args:
            question (``otter.assign.question_config.QuestionConfig``): the question config

        Returns:
            ``bool``: whether any of the test cases for the question are public
        """
        return any(not tc.hidden for tc in self._tests_by_question[question["name"]])

    def _add_test_case(self, question: QuestionConfig, test_case: TestCase):
        """
        Track a test case for the specified question.

        Args:
            question (``otter.assign.question_config.QuestionConfig``): the question config
            test_case (``TestCase``): the test case to track
        """
        self.add_question(question)
        self._tests_by_question[question.name].append(test_case)

    def _parse_test_config(self, source: list[str]) -> tuple[dict[str, Any], Union[int, None]]:
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

    def add_question(self, question: QuestionConfig):
        """
        Add a question for tracking and inclusion in the assignment summary

        Args:
            question (``otter.assign.question_config.QuestionConfig``): the question config
        """
        self._questions[question.name] = question
        if question.name not in self._tests_by_question:
            self._tests_by_question[question.name] = []

    def read_test(self, cell: nbf.NotebookNode, question: QuestionConfig):
        """
        Parse and track a test case from the provided cell for the specified question.

        Args:
            cell (``nbformat.NotebookNode``): a test cell
            question (``otter.assign.question_config.QuestionConfig``): the question config
        """
        source = get_source(cell)
        ensure_valid_syntax(source, question)

        if source[0].lstrip().startswith("#"):
            hidden = bool(re.search(r"\bhidden\b", source[0], flags=re.IGNORECASE))
        else:
            hidden = False

        test_start_line = 0 if hidden else -1

        output = ""
        for o in cell["outputs"]:
            output += "".join(o.get("text", ""))
            results = o.get("data", {}).get("text/plain")
            if results and isinstance(results, list):
                output += results[0]
            elif results:
                output += results

        config, maybe_test_start_line = self._parse_test_config(source)
        test_start_line = (
            maybe_test_start_line if maybe_test_start_line is not None else test_start_line
        )

        hidden = config.get("hidden", hidden)
        points = config.get("points", None)
        success_message = config.get("success_message", None)
        failure_message = config.get("failure_message", None)

        test_source = get_source(cell)[test_start_line + 1 :]
        test_ast = ast.parse("\n".join(test_source))
        body: str = ""
        if self.assignment.tests.ok_format:
            inp = ast.unparse(_AnnotationRemover().visit(test_ast))
            body_lines = str_to_doctest(inp.split("\n"), [])
            body_lines.extend(output.split("\n"))
            body = "\n".join(body_lines)
        else:
            if len(test_ast.body) > 2 or not isinstance(test_ast.body[0], ast.FunctionDef):
                raise ValueError(
                    f"Error in question {question.name}: an exception-based test cell may have at "
                    "most a function definition and a call to that function definition but a test "
                    f"cell with {len(test_ast.body)} nodes in its AST was encountered"
                )
            body = ast.unparse(test_ast.body[0])

        self._add_test_case(
            question,
            # TODO: does the test case need a name?
            TestCase("", body, hidden, points, success_message, failure_message),
        )

    def has_tests(self, question: QuestionConfig) -> bool:
        """
        Determine whether the specified question has any test cases.

        Args:
            question (``otter.assign.question_config.QuestionConfig``): the question config

        Returns:
            ``bool``: whether the question has any test cases
        """
        return len(self._tests_by_question.get(question.name, [])) > 0

    @staticmethod
    def _resolve_test_file_points(
        total_points: Union[int, float, list[Union[int, float, None]], None],
        test_cases: list[TestCase],
    ) -> list[TestCase]:
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

    def _create_test_file_info(self, question_name: str) -> dict[str, Any]:
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
            points = points.get("each", 1) * len(test_cases)
        elif isinstance(points, list):
            if len(points) != len(test_cases):
                raise ValueError(
                    f"Error in question {question.name}: length of 'points' is {len(points)} "
                    f"but there are {len(test_cases)} tests"
                )

        # check for errors in resolving points
        test_cases = self._resolve_test_file_points(points, test_cases)

        return {
            "name": question.name,
            "points": points,
            "all_or_nothing": question.all_or_nothing,
            "test_cases": test_cases,
        }

    @staticmethod
    def _create_ok_test_case(test_case: TestCase) -> dict[str, Any]:
        """
        Create an OK-formatted test case for a test case object.

        Args:
            test (``TestCase``): the test case to convert to OK format

        Returns:
            ``dict``: the OK-formatted test case
        """
        ret = {
            "code": test_case.body,
            "hidden": test_case.hidden,
            "locked": False,
        }

        if test_case.points is not None:
            ret["points"] = test_case.points
        if test_case.success_message:
            ret["success_message"] = test_case.success_message
        if test_case.failure_message:
            ret["failure_message"] = test_case.failure_message

        return ret

    @classmethod
    def _create_ok_test_suite(cls, test_cases: list[TestCase]) -> dict[str, Any]:
        """
        Create an OK-formatted test suite for a list of test cases.

        Args:
            test_cases (``list[TestCase]``): the test cases

        Returns:
            ``dict``: the OK-formatted test suite
        """
        return {
            "cases": [cls._create_ok_test_case(tc) for tc in test_cases],
            "scored": True,
            "setup": "",
            "teardown": "",
            "type": "doctest",
        }

    def _format_test(
        self,
        name: str,
        points: Union[int, float, list[Union[int, float, None]], None],
        all_or_nothing: bool,
        test_cases: list[TestCase],
    ) -> Union[str, dict[str, Any]]:
        """
        Format the test cases for a question based on the assignment config.

        Args:
            name (``str``): the name of the question
            points (``int | float | list[int | float | None] | None``): the ``points`` configuration
                from the question config
            all_or_nothing (``bool``): the ``all_or_nothing`` configuration from the question
                config
            test_cases (``list[TestCase]``): the test cases for the question

        Returns:
            ``dict | str``: the formatted test file
        """
        if self.assignment.tests.ok_format:
            test = {
                "name": name,
                "points": points,
            }
            # Only set all_or_nothing if it's true, since it defaults to false.
            if all_or_nothing:
                test["all_or_nothing"] = True
            test["suites"] = [self._create_ok_test_suite(test_cases)]

        else:
            template_kwargs = {
                "name": name,
                "points": points,
                "all_or_nothing": all_or_nothing,
                "test_cases": test_cases,
                "OK_FORMAT_VARNAME": OK_FORMAT_VARNAME,
            }
            test = EXCEPTION_BASED_TEST_FILE_TEMPLATE.render(**template_kwargs)

        return test

    def write_tests(
        self,
        nbmeta_config: NBMetadataConfig,
        test_dir: Union[pathlib.Path, str],
        include_hidden: bool = True,
        force_files: bool = False,
    ):
        """
        Write all test files to a notebook's metadata or a tests directory.

        Args:
            nbmeta_config (``otter.nbmeta_config.NBMetadataConfig``): the notebook metadata config
            test_dir (``pathlib.Path | str``): the tests directory
            include_hidden (``bool``): whether to include hidden test cases
            force_files (``bool``): whether to force writing to test files (overriding the
                assignment config)
        """
        use_files = self.assignment.tests.files or force_files
        if not use_files:
            nbmeta_config.tests = {}
            nbmeta_config.ok_format = self.assignment.tests.ok_format

        test_ext = ".py" if self.assignment.is_python else ".R"
        for test_name in self._tests_by_question.keys():
            if not self._tests_by_question[test_name]:
                continue

            test_info = self._create_test_file_info(test_name)
            test_path = os.path.join(test_dir, test_name + test_ext)

            if not include_hidden:
                test_info["test_cases"] = [tc for tc in test_info["test_cases"] if not tc.hidden]
                if isinstance(test_info["points"], list):
                    test_info["points"] = [
                        p
                        for tc, p in zip(test_info["test_cases"], test_info["points"])
                        if not tc.hidden
                    ]

            test = self._format_test(
                test_info["name"],
                test_info["points"],
                test_info["all_or_nothing"],
                test_info["test_cases"],
            )

            if use_files:
                with open(test_path, "w+") as f:
                    if isinstance(test, dict):
                        f.write(f"{OK_FORMAT_VARNAME} = True\n\ntest = ")
                        pprint.pprint(test, f, indent=4, width=200, depth=None)

                    else:
                        f.write(test)

            else:
                nbmeta_config.tests[test_info["name"]] = test

    def determine_question_point_value(self, question: QuestionConfig) -> Union[int, float]:
        """
        Determine the point value of a question using the question config and its test cases.

        Args:
            question (``otter.assign.question_config.QuestionConfig``): the question config

        Returns:
            ``int | float``: the point value of the question
        """
        if question.manual:
            return question.points or 0

        test_cases = self._tests_by_question.get(question.name, [])

        points = question.points
        if isinstance(points, dict):
            points = points.get("each", 1) * len(test_cases)

        if len(test_cases) == 0:
            if points is None and question.manual:
                raise ValueError(
                    f"Point value unspecified for question with no test cases: {question.name}"
                )

            return points if points is not None else 1

        try:
            resolved_test_cases = TestFile.resolve_test_file_points(points, test_cases)
        except Exception as e:
            raise type(e)(f'Error in "{question.name}" test cases: {e}')

        points = round(sum(tc.points for tc in resolved_test_cases), 5)
        return int(points) if points % 1 == 0 else points

    def generate_assignment_summary(self) -> str:
        """
        Generate a summary of the assignment's questions.

        Returns:
            ``str``: the summary
        """
        rows, manual, autograded, total = [], 0, 0, 0
        for question_name in sorted(self._tests_by_question.keys()):
            config = self._questions[question_name]
            points = self.determine_question_point_value(config)
            rows.append({"name": question_name, "points": points, "manual": config.manual})
            total += points
            if config.manual:
                manual += points
            else:
                autograded += points

        summary = f"Assignment summary:\n"
        summary += f"Total points: {total}\n"
        summary += f"Autograded:   {autograded}\n"
        summary += f"Manual:       {manual}\n\n"
        summary += str(pd.DataFrame(rows))
        return summary


def ensure_valid_syntax(source: list[str], question: QuestionConfig) -> None:
    """
    Check that a cell's source is valid Python syntax.

    Args:
        source (``list[str]``): the cell source lines

    Raises:
        ``ValueError``: if invalid syntax is found
    """
    source = "\n".join(source)
    try:
        ast.parse(source)
    except SyntaxError:
        raise ValueError(
            f"A test cell in question {question.name} contains invalid Python syntax:\n{source}"
        )


class _AnnotationRemover(ast.NodeTransformer):
    """
    An AST node transformer that removes all type annotations.
    """

    def visit(self, node: Any):
        self.generic_visit(node)
        if hasattr(node, "annotation"):
            node.annotation = None
        if hasattr(node, "returns"):
            node.returns = None
        if hasattr(node, "type_params"):
            node.type_params = None
        return node
