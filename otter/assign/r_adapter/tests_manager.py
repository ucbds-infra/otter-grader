"""R tests adapter for Otter Assign"""

import re

from dataclasses import dataclass
from typing import ClassVar

from ..constants import OTTR_TEST_FILE_TEMPLATE
from ..tests_manager import AssignmentTestsManager, TestCase
from ..utils import get_source

from ...test_files.abstract_test import TestFile


@dataclass
class RTestCase(TestCase):
    """
    A dataclass representing a test case for a question in an R assignment.
    """

    name: str
    """the name of the test case"""

    # set the type of output to ClassVar since it's not used for R test cases
    output: ClassVar[None] = None


class RAssignmentTestsManager(AssignmentTestsManager):
    """
    A class for creating and managing test cases for an R assignment.
    """

    def read_test(self, cell, question):
        source = get_source(cell)

        if source[0].lstrip().startswith("#"):
            hidden = bool(re.search(r"\bhidden\b", source[0], flags=re.IGNORECASE))
        else:
            hidden = False

        test_start_line = 0 if hidden else -1

        config, maybe_test_start_line = self._parse_test_config(source)
        test_start_line = maybe_test_start_line if maybe_test_start_line is not None else test_start_line

        test_name = config.get("name", None)
        hidden = config.get("hidden", hidden)
        points = config.get("points", None)
        success_message = config.get("success_message", None)
        failure_message = config.get("failure_message", None)

        self._add_test_case(
            question,
            RTestCase(
                '\n'.join(source[test_start_line+1:]),
                hidden,
                points,
                success_message,
                failure_message,
                test_name,
            ),
        )

    @staticmethod
    def _resolve_test_file_points(total_points, test_cases):
        return TestFile.resolve_test_file_points(total_points, test_cases)

    def _format_test(self, name, points, test_cases):
        template_data = {'name': name, 'test_cases': test_cases}
        return OTTR_TEST_FILE_TEMPLATE.render(**template_data)
