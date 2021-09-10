"""
ottr test adapters for Otter Assign
"""

import re
import pprint
import yaml
import nbformat

from collections import namedtuple

from ..constants import BEGIN_TEST_CONFIG_REGEX, END_TEST_CONFIG_REGEX, OTTR_TEST_FILE_TEMPLATE, \
    OTTR_TEST_NAME_REGEX, TEST_REGEX
from ..tests import write_test
from ..utils import get_source, lock

from ...test_files.abstract_test import TestFile


Test = namedtuple('Test', ['name', 'hidden', 'points', 'body', 'success_message', 'failure_message'])


def read_test(cell, question, assignment, rmd=False):
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
    if rmd:
        source = get_source(cell)[1:-1]
    else:
        source = get_source(cell)

    if source[0].lstrip().startswith("#"):
        hidden = bool(re.search(r"hidden", source[0], flags=re.IGNORECASE))
    else:
        hidden = False

    i = 0 if hidden else -1
    if rmd:
        i = 0

    if re.match(BEGIN_TEST_CONFIG_REGEX, source[0], flags=re.IGNORECASE):
        for i, line in enumerate(source):
            if re.match(END_TEST_CONFIG_REGEX, line, flags=re.IGNORECASE):
                break
        config = yaml.full_load("\n".join(source[1:i]))
        assert isinstance(config, dict), f"Invalid test config in cell {cell}"
    else:
        config = {}

    test_name = config.get("name", None)
    hidden = config.get("hidden", hidden)
    points = config.get("points", None)
    success_message = config.get("success_message", None)
    failure_message = config.get("failure_message", None)

    return Test(test_name, hidden, points, '\n'.join(source[i+1:]), success_message, failure_message)


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
    cell = nbformat.v4.new_code_cell()
    cell.source = ['. = ottr::check("tests/{}.R")'.format(question['name'])]

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
    lock(cell)
    return cell


def gen_suite(name, tests, points):
    """
    Generates an R-formatted test file for ottr

    Args:
        name (``str``): the test name
        tests (``list`` of ``Test``): the test case named tuples that define this test file
        points (``float`` or ``int`` or ``list`` of ``float`` or ``int``): th points per question

    Returns:
        ``str``: the rendered R test file
    """
    template_data = {'name': name, 'test_cases': tests}
    return OTTR_TEST_FILE_TEMPLATE.render(**template_data)


def remove_hidden_tests_from_dir(nb, test_dir, assignment, use_files=True):
    """
    Rewrites test files in a directory to remove hidden tests
    
    Args:
        nb (``nbformat.NotebookNode``): the student notebook
        test_dir (``pathlib.Path``): path to test files directory
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
        use_files (``bool``, optional): ignored for R assignments
    """
    for f in test_dir.iterdir():
        if f.suffix != '.R':
            continue

        with open(f) as f2:
            test = f2.read()
        
        test = re.sub(r"    ottr::TestCase\$new\(\s*hidden = TRUE[\w\W]+?^    \),?", "", test, flags=re.MULTILINE)
        test = re.sub(r",(\s*  \))", r"\1", test, flags=re.MULTILINE)  # removes a trailing comma if present

        write_test({}, f, test, use_file=True)
