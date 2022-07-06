import re

from dataclasses import replace

from .utils import Cell

from ..constants import TEST_REGEX
from ..r_adapter.tests import gen_suite
from ..utils import get_source

def is_test_cell(cell):
    """
    Returns whether the current cell is a test cell

    Args:
        cell (``otter.assign.rmarkdown_adapter.utils.Cell``): an Rmd file cell

    Returns:
        ``bool``: whether the cell is a test cell
    """
    if cell.cell_type != 'code':
        return False
    source = get_source(cell)
    return source and re.match(TEST_REGEX, source[1], flags=re.IGNORECASE)

def gen_test_cell(question, tests, tests_dict, assignment):
    """
    Parses a list of test named tuples and creates a single test file. Adds this test file as a value
    to ``tests_dict`` with a key corresponding to the test's name, taken from ``question``. Returns
    a code cell that runs the check on this test.

    Args:
        question (``dict``): question metadata
        tests (``list`` of ``Test``): tests to be written
        tests_dict (``dict``): the tests for this assignment
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations

    Returns:
        ``otter.assign.rmarkdown_adapter.utils.Cell``: code cell calling ``ottr::check`` on this test
    """
    source = f'```{{r}}\n. = ottr::check("tests/{question["name"]}.R")\n```'
    cell = Cell("code", source)

    points = question.get('points', len(tests))
    if isinstance(points, (int, float)):
        if points % len(tests) == 0:
            points = [points // len(tests) for _ in range(len(tests))]
        else:
            points = [points / len(tests) for _ in range(len(tests))]
    assert isinstance(points, list) and len(points) == len(tests), \
        f"Points for question {question['name']} could not be parsed:\n{points}"

    # update point values
    tests = [replace(tc, points=p) for tc, p in zip(tests, points)]
    test = gen_suite(question['name'], tests, points)

    tests_dict[question['name']] = test
    return cell
