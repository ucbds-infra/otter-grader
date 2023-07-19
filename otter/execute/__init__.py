"""Execution and grading internals for Otter-Grader"""

import nbformat
import pickle
import tempfile

from traitlets.config import Config

from .checker import Checker
from .preprocessor import GradingPreprocessor

from ..test_files import GradingResults
from ..utils import NBFORMAT_VERSION


def grade_notebook(
    submission_path,
    *,
    tests_glob=[],
    ignore_errors=True,
    script=False, 
    cwd=None,
    test_dir=None,
    seed=None,
    seed_variable=None,
    log=None,
    variables=None, 
    plugin_collection=None,
):
    """
    Grade an assignment file and return grade information.

    Args:
        submission_path (``str``): path to a single notebook or Python script
        tests_glob (``list[str]``): paths of test files that should be run; tests that are included
            in this list that have not already been run by the submission are run after executing
            the submission
        ignore_errors (``bool``): whether errors in execution should be ignored
        script (``bool``): whether the ``submission_path`` is a Python script
        cwd (``str``): working directory of execution to be appended to ``sys.path`` before
            executing the submission
        test_dir (``str``): path to directory of tests in the grading environment
        seed (``int``): random seed for intercell seeding
        seed_variable (``str|None``): a variable name to override with the seed
        log (``otter.check.logs.Log``): an Otter log from which to deserialize environments to grade
            questions
        variables (``dict[str, str]|None``): map of variable names -> type string to use for type
            checking values deserialized from ``log``
        plugin_collection (``otter.plugins.PluginCollection``): a set of plugins to run the
            ``before_execution`` and ``after_grading`` events on this submission

    Returns:
        ``otter.test_files.GradingResults``: the results of grading
    """
    from nbconvert.preprocessors import ExecutePreprocessor

    if not script:
        nb = nbformat.read(submission_path, as_version=NBFORMAT_VERSION)

    else:
        with open(submission_path) as f:
            nb = f.read()

        nb = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(nb)])

    if plugin_collection is not None:
        nb = plugin_collection.before_execution(nb)

    with tempfile.NamedTemporaryFile() as ntf:
        c = Config()

        # GradingPreprocessor config
        c.GradingPreprocessor.cwd = cwd
        c.GradingPreprocessor.test_dir = test_dir
        c.GradingPreprocessor.tests_glob = tests_glob
        c.GradingPreprocessor.results_path = ntf.name
        c.GradingPreprocessor.seed = seed
        c.GradingPreprocessor.seed_variable = seed_variable
        c.GradingPreprocessor.otter_log = log
        c.GradingPreprocessor.variables = variables

        # ExecutePreprocessor config
        c.ExecutePreprocessor.allow_errors = ignore_errors

        gp = GradingPreprocessor(config=c)
        ep = ExecutePreprocessor(config=c)

        nb, _ = gp.preprocess(nb)
        executed_nb, _ = ep.preprocess(nb)

        gp.cleanup()

        results = pickle.load(ntf)

    if not isinstance(results, GradingResults):
        raise TypeError("Results deserialized from grading notebook were not a GradingResults instance")

    results.notebook = executed_nb

    if plugin_collection is not None:
        plugin_collection.run("after_grading", results)

    return results
