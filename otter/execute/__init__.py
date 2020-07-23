"""
Execution and grading internals for Otter-Grader
"""

import json
import itertools
import inspect

from IPython import get_ipython

from .execute_log import execute_log
from .execute_notebook import execute_notebook, filter_ignored_cells
from .execute_script import execute_script
from .results import GradingResults
from ..test_files import TestCollection, OKTestFile
from ..utils import id_generator

def check(test_file_path, global_env=None):
    """
    Checks ``global_env`` against given ``test_file`` in OK-format. If global_env is ``None``, the 
    global environment of the calling function is used. The following two calls are equivalent:

    .. code-block:: python
        check('tests/q1.py')
        check('tests/q1.py', globals())
    
    Args:
        test_file_path (``str``): path to test file
        global_env (``dict``, optional): a global environment resulting from the execution 
            of a python script or notebook

    Returns:
        ``otter.test_files.abstract_test.TestCollectionResults``: result of running the tests in the 
            given global environment

    """
    tests = TestCollection([test_file_path], OKTestFile)

    if global_env is None:
        # Get the global env of our callers - one level below us in the stack
        # The grade method should only be called directly from user / notebook
        # code. If some other method is calling it, it should also use the
        # inspect trick to pass in its parents' global env.
        global_env = inspect.currentframe().f_back.f_globals

    return tests.run(global_env, include_grade=False)

def grade_notebook(notebook_path, tests_glob=None, name=None, ignore_errors=True, script=False, 
    cwd=None, test_dir=None, seed=None, log=None, variables=None):
    """
    Grade a notebook file & return grade information

    This function grades a single Jupyter notebook using the provided tests. If grading a Python file,
    set ``script`` to true. 

    Args:
        notebook_path (``str``): path to a single notebook
        tests_glob (``list`` of ``str``, optional): names of test files
        name (``str``, optional): initial environment name
        ignore_errors (``bool``, optional): whether errors in execution should be ignored
        script (``bool``, optional): whether the notebook_path is a Python script
        cwd (``str``, optional): working directory of execution to be appended to ``sys.path`` in 
            grading environment
        test_dir (``str``, optional): path to directory of tests in grading environment
        seed (``int``, optional): random seed for intercell seeding
        log (``otter.check.logs.Log``, optional): log from which to grade questions
        variables (``dict``, optional): map of variable names -> type string to check type of deserialized
            object to prevent arbitrary code from being put into the environment; ignored if log is ``None``

    Returns:
        ``otter.execute.results.GradingResults``: the results of grading
    """
    # ensure this is not being executed inside a notebook
    assert get_ipython() is None, "Cannot execute inside Jupyter Notebook"

    if not script:
        try:
            with open(notebook_path) as f:
                nb = json.load(f)
        except UnicodeDecodeError:
            with open(notebook_path, encoding='utf-8') as f:
                nb = json.load(f)
    else:
        with open(notebook_path) as f:
            nb = f.read()

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
        global_env = execute_log(nb, log, secret, initial_env, ignore_errors=ignore_errors, cwd=cwd, test_dir=test_dir, variables=variables)
    elif script:
        global_env = execute_script(nb, secret, initial_env, ignore_errors=ignore_errors, cwd=cwd, seed=seed)
    else:
        global_env = execute_notebook(nb, secret, initial_env, ignore_errors=ignore_errors, cwd=cwd, test_dir=test_dir, seed=seed)

    test_results = global_env[results_array]

    # Check for tests which were not included in the notebook and specified by tests_globs
    # Allows instructors to run notebooks with additional tests not accessible to user
    if tests_glob:
        # unpack list of paths into a single list
        tested_set = list(itertools.chain(*[r.paths for r in test_results]))
        extra_tests = []
        for t in sorted(tests_glob):
            include = True
            for tested in tested_set:
                if tested in t:     # e.g. if 'tests/q1.py' is in /srv/repo/lab01/tests/q1.py'
                    include = False
            if include:
                extra_tests.append(TestCollection([t], OKTestFile))
        extra_results = [t.run(global_env, include_grade=False) for t in extra_tests]
        test_results += extra_results

    return GradingResults(test_results)
