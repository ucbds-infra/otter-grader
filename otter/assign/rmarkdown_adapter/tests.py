import re

from .utils import create_cell

from ..constants import TEST_REGEX
from ..r_adapter.tests import gen_suite
from ..utils import get_source

from ...test_files.abstract_test import TestFile


def is_test_cell(cell):
    """
    Returns whether the current cell is a test cell
    
    Args:
        cell (``nbformat.NotebookNode``): an Rmd file cell

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
        ``nbformat.NotebookNode``: code cell calling ``ottr::check`` on this test
    """
    source = f'```{{r}}\n. = ottr::check("tests/{question["name"]}.R")\n```'
    cell = create_cell("code", source)

    points = question.get('points', None)
    if isinstance(points, dict):
        points = points.get('each', 1) * len(tests)
    elif isinstance(points, list):
        if len(points) != len(tests):
            raise ValueError(
                f"Error in question {question['name']}: length of 'points' is {len(points)} but there "
                f"are {len(tests)} tests")

    # check for errors in resolving points
    tests = TestFile.resolve_test_file_points(points, tests)

    test = gen_suite(question['name'], tests, points)

    tests_dict[question['name']] = test
    return cell
