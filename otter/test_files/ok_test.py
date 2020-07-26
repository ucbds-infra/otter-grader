"""
Support for OK-formatted test files
"""

import os
import io
import doctest
import warnings
import pathlib

from contextlib import redirect_stderr, redirect_stdout
from textwrap import dedent

from .abstract_test import TestFile
from ..utils import hide_outputs

def run_doctest(name, doctest_string, global_environment):
    """
    Run a single test with given ``global_environment``. Returns ``(True, '')`` if the doctest passes. 
    Returns ``(False, failure_message)`` if the doctest fails.

    Args:
        name (``str``): name of doctest
        doctest_string (``str``): doctest in string form
        global_environment (``dict``): global environment resulting from the execution of a python 
            script/notebook
    
    Returns:
        ``tuple`` of (``bool``, ``str``): results from running the test
    """
    examples = doctest.DocTestParser().parse(
        doctest_string,
        name
    )
    test = doctest.DocTest(
        [e for e in examples if isinstance(e, doctest.Example)],
        global_environment,
        name,
        None,
        None,
        doctest_string
    )

    doctestrunner = doctest.DocTestRunner(verbose=True)

    runresults = io.StringIO()
    with redirect_stdout(runresults), redirect_stderr(runresults), hide_outputs():
        doctestrunner.run(test, clear_globs=False)
    with open(os.devnull, 'w') as f, redirect_stderr(f), redirect_stdout(f):
        result = doctestrunner.summarize(verbose=True)
    # An individual test can only pass or fail
    if result.failed == 0:
        return (True, '')
    else:
        return False, runresults.getvalue()

class OKTestFile(TestFile):
    """
    A single test (set of doctests) for Otter.
    
    Instances of this class are callable. When called, it takes a ``global_environment`` dict, and returns 
    an ``otter.ok_parser.OKTestsResult`` object. We only take a global_environment, *not* a 
    ``local_environment``. This makes tests not useful inside functions, methods or other scopes with 
    local variables. This is a limitation of doctest, so we roll with it.

    The last 2 attributes (``passed``, ``failed_test``) are set after calling ``run()``.

    Args:
        name (``str``): name of test
        tests (``list`` of ``str``): ;ist of docstring tests to be run
        hiddens (``list`` of ``bool``): visibility of each tests in ``tests``
        value (``int``, optional): point value of this test, defaults to 1
        hidden (``bool``, optional): wheter this test is hidden
    """

    def run(self, global_environment):
        """Runs tests on a given ``global_environment``
        
        Arguments:
            ``global_environment`` (``dict``): result of executing a Python notebook/script
        
        Returns:
            ``tuple`` of (``bool``, ``otter.ok_parser.OKTest``): whether the test passed and a pointer 
                to the current ``otter.ok_parser.OKTest`` object
        """
        for i, t in enumerate(self.public_tests + self.hidden_tests):
            passed, result = run_doctest(self.name + ' ' + str(i), t, global_environment)
            if not passed:
                self.passed = False
                self.failed_test = t
                self.failed_test_hidden = i >= len(self.public_tests)
                self.result = result
                return False, self
        self.passed = True
        return True, self

    @classmethod
    def from_file(cls, path):
        """
        Parse an ok test file & return an ``OKTest``

        Args:
            path (``str``): path to ok test file

        Returns:
            ``otter.ok_parser.OKTest``: new ``OKTest`` object created from the given file
        """
        # ok test files are python files, with a global 'test' defined
        test_globals = {}
        with open(path) as f:
            exec(f.read(), test_globals)

        test_spec = test_globals['test']

        # We only support a subset of these tests, so let's validate!

        # Make sure there is a name
        assert 'name' in test_spec

        # Do not support multiple suites in the same file
        assert len(test_spec['suites']) == 1

        test_suite = test_spec['suites'][0]

        # Only support doctest. I am unsure if other tests are implemented
        assert test_suite.get('type', 'doctest') == 'doctest'

        # Not setup and teardown supported
        assert not bool(test_suite.get('setup'))
        assert not bool(test_suite.get('teardown'))

        if 'hidden' in test_spec:
            warnings.warn(
                "The global 'hidden' key of ok-tests is deprecated since v1.0.0. "
                "This key will be ignored.", 
                FutureWarning
            )

        tests = []
        hiddens = []

        for _, test_case in enumerate(test_spec['suites'][0]['cases']):
            tests.append(dedent(test_case['code']))
            hiddens.append(test_case.get('hidden', True))

        # convert path into PurePosixPath for test name
        name = str(pathlib.Path(path).as_posix())

        return cls(name, tests, hiddens, test_spec.get('points', 1), test_spec.get('hidden', True))
