"""
Execution and grading internals for Otter-Grader
"""

import json
import inspect
import itertools
import nbformat

from IPython import get_ipython

from .execute_log import execute_log
from .execute_notebook import execute_notebook
from .transforms import filter_ignored_cells, script_to_notebook

from ..test_files import GradingResults, NotebookMetadataOKTestFile, OKTestFile
from ..utils import id_generator


NBFORMAT_VERSION = 4


def check(nb_or_test_path, test_name=None, global_env=None):
    """
    Checks a global environment against given test file. If global_env is ``None``, the global 
    environment of the calling frame is used; i.e., the following two calls are equivalent:

    .. code-block:: python

        check('tests/q1.py')
        check('tests/q1.py', globals())
    
    Args:
        nb_or_test_path (``str``): path to test file or notebook
        test_name (``str``, optional): the name of the test if a notebook metadata test
        global_env (``dict``, optional): a global environment resulting from the execution 
            of a python script or notebook

    Returns:
        ``otter.test_files.abstract_test.TestFile``: result of running the tests in the 
        given global environment
    """
    if test_name is None:
        test = OKTestFile.from_file(nb_or_test_path)
    else:
        test = NotebookMetadataOKTestFile.from_file(nb_or_test_path, test_name)

    if global_env is None:
        # Get the global env of our callers - one level below us in the stack
        # The grade method should only be called directly from user / notebook
        # code. If some other method is calling it, it should also use the
        # inspect trick to pass in its parents' global env.
        global_env = inspect.currentframe().f_back.f_globals

    test.run(global_env)

    return test


def grade_notebook(submission_path, *, tests_glob=None, name=None, ignore_errors=True, script=False, 
    cwd=None, test_dir=None, seed=None, seed_variable=None, log=None, variables=None, 
    plugin_collection=None):
    """
    Grade an assignment file and return grade information

    Args:
        submission_path (``str``): path to a single notebook or Python script
        tests_glob (``list`` of ``str``, optional): paths to test files to run
        name (``str``, optional): initial environment name
        ignore_errors (``bool``, optional): whether errors in execution should be ignored
        script (``bool``, optional): whether the ``submission_path`` is a Python script
        cwd (``str``, optional): working directory of execution to be appended to ``sys.path`` in 
            grading environment
        test_dir (``str``, optional): path to directory of tests in grading environment
        seed (``int``, optional): random seed for intercell seeding
        seed_variable (``str``, optional): a variable name to override with the seed
        log (``otter.check.logs.Log``, optional): log from which to grade questions
        variables (``dict``, optional): map of variable names -> type string to check type of deserialized
            object to prevent arbitrary code from being put into the environment; ignored if log is ``None``
        plugin_collection (``otter.plugins.PluginCollection``, optional): a set of plugins to run on
            this assignment during execution and grading

    Returns:
        ``otter.test_files.GradingResults``: the results of grading
    """
    if not script:
        nb = nbformat.read(submission_path, as_version=NBFORMAT_VERSION)

    else:
        with open(submission_path) as f:
            nb = f.read()

        nb = script_to_notebook(nb)

    if plugin_collection is not None:
        nb = plugin_collection.before_execution(nb)

    # remove any ignored cells from the notebook
    if not script:
        nb = filter_ignored_cells(nb)

    secret = id_generator()
    results_array = "check_results_{}".format(secret)
    initial_env = {
        results_array: []
    }

    if name:
        initial_env["__name__"] = name

    if log is not None:
        global_env = execute_log(
            nb, log, secret, initial_env, ignore_errors=ignore_errors, cwd=cwd, test_dir=test_dir, 
            variables=variables)

    else:
        global_env = execute_notebook(
            nb, results_array, initial_env, ignore_errors=ignore_errors, cwd=cwd, test_dir=test_dir, 
            seed=seed, seed_variable=seed_variable)

    if plugin_collection is not None:
        plugin_collection.run("after_execution", global_env)

    tests_run = global_env[results_array]

    # Check for tests which were not included in the notebook and specified by tests_globs
    # Allows instructors to run notebooks with additional tests not accessible to user
    if tests_glob:
        # unpack list of paths into a single list
        tested_set = [test.path for test in tests_run]
        extra_tests = []
        for t in sorted(tests_glob):
            include = True
            for tested in tested_set:
                if tested in t or t in tested:     # e.g. if 'tests/q1.py' is in /srv/repo/lab01/tests/q1.py
                    include = False

            if include:
                extra_tests.append(OKTestFile.from_file(t))
                extra_tests[-1].run(global_env)

        tests_run += extra_tests

    results = GradingResults(tests_run)

    if plugin_collection is not None:
        plugin_collection.run("after_grading", results)
    
    return results
