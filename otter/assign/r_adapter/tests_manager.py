"""
ottr test adapters for Otter Assign
"""

import re

from dataclasses import dataclass
from typing import ClassVar

from ..constants import BEGIN_TEST_CONFIG_REGEX, END_TEST_CONFIG_REGEX, OTTR_TEST_FILE_TEMPLATE
from ..tests_manager import AssignmentTestsManager, TestCase
from ..utils import get_source, lock

from ...test_files.abstract_test import TestFile


# TODO: docstrings

@dataclass
class RTestCase(TestCase):

    name: str

    output: ClassVar[None] = None


class RAssignmentTestsManager(AssignmentTestsManager):

    def read_test(self, cell, question):
        """
        Returns the contents of a test as a ``(name, hidden, body)`` named tuple
        
        Args:
            cell (``nbformat.NotebookNode``): a test cell
            question (``dict``): question metadata
            assignment (``otter.assign.assignment.Assignment``): the assignment configurations
            rmd (``bool``, optional): whether the cell is from an Rmd file; if true, the first and last
                lines of ``cell``'s source are trimmed, since they should be backtick delimeters

        Returns:
            ``Test``: test named tuple
        """
        # TODO: i don't think this is needed...?
        # if self.assignment.is_rmd:
        #     source = get_source(cell)[1:-1]
        # else:
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

    # TODO: why is points ignored here?
    def _format_test(self, name, points, test_cases):
        """
        Generates an R-formatted test file for ottr

        Args:
            name (``str``): the test name
            tests (``list`` of ``Test``): the test case named tuples that define this test file
            points (``float`` or ``int`` or ``list`` of ``float`` or ``int``): th points per question

        Returns:
            ``str``: the rendered R test file
        """
        template_data = {'name': name, 'test_cases': test_cases}
        return OTTR_TEST_FILE_TEMPLATE.render(**template_data)
