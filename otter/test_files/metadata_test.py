"""
Support for notebook metadata test files
"""

import os
import io
import json
import doctest
import warnings
import pathlib

from contextlib import redirect_stderr, redirect_stdout
from textwrap import dedent

from .abstract_test import TestCase
from .ok_test import OKTestFile
from ..utils import hide_outputs


NOTEBOOK_METADATA_KEY = "otter"


class NotebookMetadataTestFile(OKTestFile):
    """
    A single notebook metadata test file for Otter.

    Tests are defined in the metadata of a jupyter notebook as a JSON object with the ``otter`` key.
    The tests themselves are OK-formatted.

    .. code-block:: json

    {
        "metadata": {
            "otter": {
                "tests": {
                    "q1": {}
                }
            }
        }
    }

    Args:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list`` of ``TestCase``): a list of parsed tests to be run
        value (``int``, optional): the point value of this test, defaults to 1
        all_or_nothing (``bool``, optional): whether the test should be graded all-or-nothing across
            cases

    Attributes:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list`` of ``TestCase``): a list of parsed tests to be run
        value (``int``): the point value of this test, defaults to 1
        all_or_nothing (``bool``): whether the test should be graded all-or-nothing across
            cases
        passed_all (``bool``): whether all of the test cases were passed
        test_case_results (``list`` of ``TestCaseResult``): a list of results for the test cases in
            ``test_cases``
        grade (``float``): the percentage of ``points`` earned for this test file as a decimal
    """

    @classmethod
    def from_file(cls, path, test_name):
        """
        Parse an ok test file & return an ``OKTest``

        Args:
            path (``str``): path to ok test file

        Returns:
            ``otter.ok_parser.OKTest``: new ``OKTest`` object created from the given file
        """
        with open(path) as f:
            nb = json.load(f)
        
        test_spec = nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"]
        if test_name not in test_spec:
            raise ValueError(f"Test {test_name} not found")
        
        test_spec = test_spec[test_name]

        # We only support a subset of these tests, so let's validate!

        # Make sure there is a name
        # assert 'name' in test_spec

        # Do not support multiple suites in the same file
        assert len(test_spec['suites']) == 1

        test_suite = test_spec['suites'][0]

        # Only support doctest. I am unsure if other tests are implemented
        assert test_suite.get('type', 'doctest') == 'doctest'

        # Not setup and teardown supported
        assert not bool(test_suite.get('setup'))
        assert not bool(test_suite.get('teardown'))

        test_cases = []
        # hiddens = []

        for i, test_case in enumerate(test_spec['suites'][0]['cases']):
            test_cases.append(TestCase(
                name = test_case.get('name', f"{test_spec['name']}_{i + 1}"),
                body = dedent(test_case['code']), 
                hidden = test_case.get('hidden', True)
            ))
            # tests.append(dedent(test_case['code']))
            # hiddens.append(test_case.get('hidden', True))

        # convert path into PurePosixPath for test name
        path = str(pathlib.Path(path).as_posix())

        # grab whether the tests are all-or-nothing
        all_or_nothing = test_spec.get('all_or_nothing', True)

        return cls(test_name, path, test_cases, test_spec.get('points', 1), all_or_nothing)
