"""OK-formatted test parsers and builders for Otter Assign"""

import nbformat
import os
import pprint
import re
import yaml

from collections import namedtuple

from .constants import BEGIN_TEST_CONFIG_REGEX, END_TEST_CONFIG_REGEX, EXCEPTION_BASED_TEST_FILE_TEMPLATE
from .r_adapter.tests import gen_suite as gen_suite_ottr
from .solutions import remove_ignored_lines
from .utils import get_source, lock, str_to_doctest

from ..test_files.abstract_test import OK_FORMAT_VARNAME, TestFile
from ..test_files.metadata_test import NOTEBOOK_METADATA_KEY


Test = namedtuple('Test', ['input', 'output', 'hidden', 'points', 'success_message', 'failure_message'])


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
    source = get_source(cell)
    if source[0].lstrip().startswith("#"):
        hidden = bool(re.match(r"#\s+hidden\s*", source[0], flags=re.IGNORECASE))
    else:
        hidden = False

    i = 0 if hidden else -1

    output = ''
    for o in cell['outputs']:
        output += ''.join(o.get('text', ''))
        results = o.get('data', {}).get('text/plain')
        if results and isinstance(results, list):
            output += results[0]
        elif results:
            output += results

    if re.match(BEGIN_TEST_CONFIG_REGEX, source[0], flags=re.IGNORECASE):
        for i, line in enumerate(source):
            if re.match(END_TEST_CONFIG_REGEX, line, flags=re.IGNORECASE):
                break
        config = yaml.full_load("\n".join(source[1:i]))
        assert isinstance(config, dict), f"Invalid test config in cell {cell}"
    else:
        config = {}
    
    hidden = config.get("hidden", hidden)
    points = config.get("points", None)
    success_message = config.get("success_message", None)
    failure_message = config.get("failure_message", None)

    test_source = "\n".join(remove_ignored_lines(get_source(cell)[i+1:]))

    return Test(test_source, output, hidden, points, success_message, failure_message)


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
                f"are {len(tests)} tests")

    # check for errors in resolving points
    TestFile.resolve_test_file_points(points, tests)

    test_info = {
        "name": question["name"],
        "points": points,
        "test_cases": tests,
    }

    tests_dict[question['name']] = test_info
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


def write_tests(nb, test_dir, test_files, assignment, include_hidden=True, force_files=False):
    """
    """
    # TODO: move this notebook to the notebook metadata test classes
    if isinstance(nb, dict) and not assignment.tests["files"]:
        if NOTEBOOK_METADATA_KEY not in nb["metadata"]:
            nb["metadata"][NOTEBOOK_METADATA_KEY] = {}
        nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"] = {}
        nb["metadata"][NOTEBOOK_METADATA_KEY][OK_FORMAT_VARNAME] = assignment.tests["ok_format"]

    test_ext = ".py" if assignment.is_python else ".R"
    for test_name, test_info in test_files.items():
        test_path = os.path.join(test_dir, test_name + test_ext)
        name, points, test_cases = test_info["name"], test_info["points"], test_info["test_cases"]

        if not include_hidden:
            test_cases = [tc for tc in test_cases if not tc.hidden]

        if assignment.is_r:
            test = gen_suite_ottr(name, test_cases, points)

        elif assignment.tests["ok_format"]:
            test = {
                "name": name,
                "points": points,
                "suites": [gen_suite(test_cases)],
            }

        else:
            template_kwargs = {
                "name": name, 
                "points": points, 
                "test_cases": test_cases, 
                "OK_FORMAT_VARNAME": OK_FORMAT_VARNAME,
            }
            test = EXCEPTION_BASED_TEST_FILE_TEMPLATE.render(**template_kwargs)

        if assignment.tests["files"] or force_files:
            with open(test_path, "w+") as f:
                if isinstance(test, dict):
                    f.write(f"{OK_FORMAT_VARNAME} = True\n\ntest = ")
                    pprint.pprint(test, f, indent=4, width=200, depth=None)

                else:
                    f.write(test)

        else:
            # TODO: move this notebook to the notebook metadata test classes
            nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"][name] = test


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
            write_test({}, f, test, use_file=True) # TODO: fix
    else:
        tests = nb["metadata"].get(NOTEBOOK_METADATA_KEY, {}).get("tests", {})
        for tn, test in tests.items():
            for i, tc in list(enumerate(test["suites"][0]["cases"]))[::-1]:
                if tc["hidden"]:
                    test["suites"][0]["cases"].pop(i)


def determine_question_point_value(question_metadata, test_cases):
    """
    Determine the point value of a question using the question metadata and list of test cases.

    Args:
        question_metadata (``dict[str, object]``): the question metadata
        test_cases (``list[Test]``): the test cases for the question; if a manual question, this list
            should be empty

    Returns:
        number: the point value of the question
    """
    if len(test_cases) == 0:
        if question_metadata["points"] is None and question_metadata["manual"]:
            raise ValueError(f"Point value unspecified for question with no test cases: {question_metadata['name']}")

        return question_metadata["points"] if question_metadata["points"] is not None else 1

    resolved_test_cases = TestFile.resolve_test_file_points(question_metadata["points"], test_cases)
    points = round(sum(tc.points for tc in resolved_test_cases), 5)
    return int(points) if points % 1 == 0 else points
