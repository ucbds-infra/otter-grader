"""
OK-formatted test parsers and builders for Otter Assign
"""

import re
import pprint
import yaml
import nbformat

from collections import namedtuple

from .constants import BEGIN_TEST_CONFIG_REGEX, END_TEST_CONFIG_REGEX, TEST_REGEX, OTTR_TEST_NAME_REGEX, \
    OTTR_TEST_FILE_TEMPLATE
from .utils import get_source, lock, str_to_doctest
from ...test_files.abstract_test import TestFile
from ...test_files.metadata_test import NOTEBOOK_METADATA_KEY


Test = namedtuple('Test', ['input', 'output', 'hidden', 'points', 'success_message', 'failure_message'])


def is_test_cell(cell):
    """
    Returns whether the current cell is a test cell
    
    Args:
        cell (``nbformat.NotebookNode``): a notebook cell

    Returns:
        ``bool``: whether the cell is a test cell
    """
    if cell.cell_type != 'code':
        return False
    source = get_source(cell)
    return source and re.match(TEST_REGEX, source[0], flags=re.IGNORECASE)


def any_public_tests(test_cases):
    """
    Returns whether any of the ``Test`` named tuples in ``test_cases`` are public tests.

    Args:
        test_cases (``list`` of ``Test``): list of test cases
    
    Returns:
        ``bool``: whether any of the tests are public
    """
    return any(not test.hidden for test in test_cases)


def read_test(cell, question, assignment):
    """
    Returns the contents of a test as an ``(input, output, hidden, points, success_message, 
    failure_message)`` named tuple
    
    Args:
        cell (``nbformat.NotebookNode``): a test cell
        question (``dict``): question metadata
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations

    Returns:
        ``Test``: test named tuple
    """
    hidden = bool(re.search("hidden", get_source(cell)[0], flags=re.IGNORECASE))
    output = ''
    for o in cell['outputs']:
        output += ''.join(o.get('text', ''))
        results = o.get('data', {}).get('text/plain')
        if results and isinstance(results, list):
            output += results[0]
        elif results:
            output += results

    lines = get_source(cell)

    if re.match(BEGIN_TEST_CONFIG_REGEX, lines[0], flags=re.IGNORECASE):
        for i, line in enumerate(lines):
            if re.match(END_TEST_CONFIG_REGEX, line, flags=re.IGNORECASE):
                break
        config = yaml.full_load("\n".join(lines[1:i]))
        assert isinstance(config, dict), f"Invalid test config in cell {cell}"
    else:
        config = {}
        i = 0
    
    hidden = config.get("hidden", hidden)
    points = config.get("points", None)
    success_message = config.get("success_message", None)
    failure_message = config.get("failure_message", None)

    return Test('\n'.join(get_source(cell)[i+1:]), output, hidden, points, success_message, failure_message)


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
        ``nbformat.NotebookNode``: code cell calling ``otter.Notebook.check`` on this test
    """
    cell = nbformat.v4.new_code_cell()

    cell.source = ['grader.check("{}")'.format(question['name'])]

    points = question.get('points', None)
    if isinstance(points, dict):
        points = points.get('each', 1) * len(tests)
    elif isinstance(points, list):
        if len(points) != len(tests):
            raise ValueError(
                f"Error in question {question['name']}: length of 'points' is {len(points)} but there "
                f"are {len(tests)} tests"
            )

    # check for errors in resolving points
    TestFile.resolve_test_file_points(points, tests)

    suites = [gen_suite(tests)]
    test = {
        'name': question['name'],
        'points': points,
        'suites': suites,
    }

    tests_dict[question['name']] = test
    lock(cell)
    return cell


def gen_suite(tests):
    """
    Generates an OK test suite for a list of tests as named tuples
    
    Args:
        tests (``list`` of ``otter.assign.Test``): test cases

    Returns:
        ``dict``: OK test suite
    """
    cases = [gen_case(test) for test in tests]
    return  {
      'cases': cases,
      'scored': True,
      'setup': '',
      'teardown': '',
      'type': 'doctest'
    }


def gen_case(test):
    """
    Generates an OK test case for a test named tuple
    
    Args:
        test (``otter.assign.Test``): OK test for this test case

    Returns:
        ``dict``: the OK test case
    """
    code_lines = str_to_doctest(test.input.split('\n'), [])
    code_lines.append(test.output)
    ret = {
        'code': '\n'.join(code_lines),
        'hidden': test.hidden,
        'locked': False,
    }
    if test.points is not None:
        ret['points'] = test.points
    if test.success_message:
        ret['success_message'] = test.success_message
    if test.failure_message:
        ret['failure_message'] = test.failure_message
    return ret


def write_test(nb, path, test, use_file=False):
    """
    Writes an OK test file
    
    Args:
        nb (``dict``): the notebook being written
        path (``str``): path of file to be written or the name of the test
        test (``dict``): OK test to be written
        use_file (``bool``): whether to write to a file instead of putting the test in the notebook
            metadata
    """
    if use_file:
        with open(path, 'w+') as f:
            if isinstance(test, dict):
                f.write('test = ')
                pprint.pprint(test, f, indent=4, width=200, depth=None)
            else:
                f.write(test)
    else:
        if NOTEBOOK_METADATA_KEY not in nb["metadata"]:
            nb["metadata"][NOTEBOOK_METADATA_KEY] = {}
        if "tests" not in nb["metadata"][NOTEBOOK_METADATA_KEY]:
            nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"] = {}
        nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"][path] = test


def remove_hidden_tests_from_dir(nb, test_dir, assignment, use_files=False):
    """
    Rewrites test files in a directory to remove hidden tests
    
    Args:
        nb (``dict``): the notebook being written
        test_dir (``pathlib.Path``): path to test files directory
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
        use_file (``bool``): whether separate test files were written instead of notebook metadata
    """
    if use_files:
        for f in test_dir.iterdir():
            if f.name == '__init__.py' or f.suffix != '.py':
                continue
            locals = {}
            with open(f) as f2:
                exec(f2.read(), globals(), locals)
            test = locals['test']
            for suite in test['suites']:
                for i, case in list(enumerate(suite['cases']))[::-1]:
                    if case['hidden']:
                        suite['cases'].pop(i)
                        if isinstance(test['points'], list):
                            test['points'].pop(i)
            write_test({}, f, test, use_file=True)
    else:
        tests = nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"]
        for tn, test in tests.items():
            for i, tc in list(enumerate(test["suites"][0]["cases"]))[::-1]:
                if tc["hidden"]:
                    test["suites"][0]["cases"].pop(i)
