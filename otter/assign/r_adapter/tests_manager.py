"""R tests adapter for Otter Assign"""

import nbformat
import re

from jinja2 import Template
from textwrap import indent
from typing import Optional, Union

from ..question_config import QuestionConfig
from ..tests_manager import AssignmentTestsManager
from ...test_files.abstract_test import TestCase, TestFile
from ...utils import get_source


# DON'T change this template or the regex that removes hidden tests will break in the R adapter!
OTTR_TEST_FILE_TEMPLATE = Template(
    """\
test = list(
  name = "{{ name }}",
  cases = list({% for tc in test_cases %}
    ottr::TestCase$new(
      hidden = {% if tc.hidden %}TRUE{% else %}FALSE{% endif %},
      name = {% if tc.name %}"{{ tc.name }}"{% else %}NA{% endif %},
      points = {% if tc.points is none %}NA{% else %}{{ tc.points }}{% endif %},{% if tc.success_message %}
      success_message = "{{ tc.success_message }}",{% endif %}{% if tc.failure_message %}
      failure_message = "{{ tc.failure_message }}",{% endif %}
      code = {
        {{ indent(tc.body, "        ").lstrip() }}{# lstrip so that the first line indent is correct #}
      }
    ){% if not loop.last %},{% endif %}{% endfor %}
  )
)"""
)
OTTR_TEST_FILE_TEMPLATE.globals["indent"] = indent


class RAssignmentTestsManager(AssignmentTestsManager):
    """
    A class for creating and managing test cases for an R assignment.
    """

    def read_test(self, cell: nbformat.NotebookNode, question: QuestionConfig):
        source = get_source(cell)

        if source[0].lstrip().startswith("#"):
            hidden = bool(re.search(r"\bhidden\b", source[0], flags=re.IGNORECASE))
        else:
            hidden = False

        test_start_line = 0 if hidden else -1

        config, maybe_test_start_line = self._parse_test_config(source)
        test_start_line = (
            maybe_test_start_line if maybe_test_start_line is not None else test_start_line
        )

        test_name = config.get("name", None)
        hidden = config.get("hidden", hidden)
        points = config.get("points", None)
        success_message = config.get("success_message", None)
        failure_message = config.get("failure_message", None)

        self._add_test_case(
            question,
            TestCase(
                test_name,
                "\n".join(source[test_start_line + 1 :]),
                hidden,
                points,
                success_message,
                failure_message,
            ),
        )

    @staticmethod
    def _resolve_test_file_points(
        total_points: Optional[Union[int, float, list[Optional[Union[int, float]]]]],
        test_cases: list[TestCase],
    ) -> list[TestCase]:
        return TestFile.resolve_test_file_points(total_points, test_cases)

    def _format_test(
        self,
        name: str,
        points: Optional[Union[int, float, list[Optional[Union[int, float]]]]],
        all_or_nothing: bool,
        test_cases: list[TestCase],
    ) -> str:
        template_data = {"name": name, "test_cases": test_cases}
        return OTTR_TEST_FILE_TEMPLATE.render(**template_data)
