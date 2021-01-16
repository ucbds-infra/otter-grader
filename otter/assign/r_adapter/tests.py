"""
ottr test adapters for Otter Assign
"""

import re
import pprint
import yaml
import nbformat

from collections import namedtuple

from ..constants import TEST_REGEX, OTTR_TEST_NAME_REGEX, OTTR_TEST_FILE_TEMPLATE
from ..tests import write_test
from ..utils import get_source, lock

Test = namedtuple('Test', ['name', 'hidden', 'body'])

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
    hidden = bool(re.search("hidden", source[0], flags=re.IGNORECASE))
    lines = source[1:]
    assert sum("test_that(" in line for line in lines) == 1, \
        f"Too many test_that calls in test cell (max 1 allowed):\n{cell}"
    test_name = None
    for line in lines:
        match = re.match(OTTR_TEST_NAME_REGEX, line)
        if match:
            test_name = match.group(1)
            break
    assert test_name is not None, f"Could not parse test name:\n{cell}"
    return Test(test_name, hidden, '\n'.join(lines))

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

    points = question.get('points', len(tests))
    if isinstance(points, int):
        if points % len(tests) == 0:
            points = [points // len(tests) for _ in range(len(tests))]
        else:
            points = [points / len(tests) for _ in range(len(tests))]
    assert isinstance(points, list) and len(points) == len(tests), \
        f"Points for question {question['name']} could not be parsed:\n{points}"

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
    metadata = {'name': name, 'cases': []}
    cases = metadata['cases']
    for test, p in zip(tests, points):
        cases.append({
            'name': test.name,
            'points': p,
            'hidden': test.hidden
        })
    
    metadata = yaml.dump(metadata)

    return OTTR_TEST_FILE_TEMPLATE.render(
        metadata = metadata,
        tests = tests
    )

def remove_hidden_tests_from_dir(test_dir, assignment):
    """
    Rewrites test files in a directory to remove hidden tests
    
    Args:
        test_dir (``pathlib.Path``): path to test files directory
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
    """
    for f in test_dir.iterdir():
        if f.suffix != '.R':
            continue

        with open(f) as f2:
            test = f2.read()
        
        metadata, in_metadata, start_lines, test_names = "", False, {}, []
        metadata_start, metadata_end = -1, -1
        lines = test.split("\n")
        for i, line in enumerate(lines):
            match = re.match(OTTR_TEST_NAME_REGEX, line)
            if line.strip() == "test_metadata = \"":
                in_metadata = True
                metadata_start = i
            elif in_metadata and line.strip() == "\"":
                in_metadata = False
                metadata_end = i
            elif in_metadata:
                metadata += line + "\n"
            elif match:
                test_name = match.group(1)
                test_names.append(test_name)
                start_lines[test_name] = i

        assert metadata and metadata_start != -1 and metadata_end != -1, \
            f"Failed to parse test metadata in {f}"
        metadata = yaml.full_load(metadata)
        cases = metadata['cases']

        lines_to_remove, cases_to_remove = [], []
        for i, case in enumerate(cases):
            if case['hidden']:
                start_line = start_lines[case['name']]
                try:
                    next_test = test_names[test_names.index(case['name']) + 1]
                    end_line = start_lines[next_test]
                except IndexError:
                    end_line = len(lines)
                lines_to_remove.extend(range(start_line, end_line))
                cases_to_remove.append(i)

        metadata['cases'] = [c for i, c in enumerate(cases) if i not in set(cases_to_remove)]
        lines = [l for i, l in enumerate(lines) if i not in set(lines_to_remove)]
        lines[metadata_start:metadata_end + 1] = ["test_metadata = \""] + \
            yaml.dump(metadata).split("\n") + ["\""]
        test = "\n".join(lines)

        write_test(f, test)
