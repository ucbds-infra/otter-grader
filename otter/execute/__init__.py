"""Execution and grading internals for Otter-Grader"""

import nbformat
import os
import pickle
import tempfile

from traitlets.config import Config
from typing import Optional, TYPE_CHECKING

from .checker import Checker
from .logging import start_server
from ..plugins import PluginCollection
from ..test_files import GradingResults
from ..utils import NBFORMAT_VERSION


__all__ = ["Checker", "grade_notebook"]


def grade_notebook(
    submission_path: str,
    *,
    tests_glob: Optional[list[str]] = None,
    ignore_errors: bool = True,
    script: bool = False,
    cwd: Optional[str] = None,
    test_dir: Optional[str] = None,
    seed: Optional[int] = None,
    seed_variable: Optional[str] = None,
    log: Optional["Log"] = None,
    variables: Optional[dict[str, str]] = None,
    plugin_collection: Optional[PluginCollection] = None,
    force_python3_kernel: bool = True,
):
    """
    Grade an assignment file and return grade information.

    Args:
        submission_path (``str``): path to a single notebook or Python script
        tests_glob (``list[str] | NOne``): paths of test files that should be run; tests that are
            included in this list that have not already been run by the submission are run after
            executing the submission
        ignore_errors (``bool``): whether errors in execution should be ignored
        script (``bool``): whether the ``submission_path`` is a Python script
        cwd (``str | None``): working directory of execution to be appended to ``sys.path`` before
            executing the submission
        test_dir (``str | None``): path to directory of tests in the grading environment
        seed (``int | None``): random seed for intercell seeding
        seed_variable (``str | None``): a variable name to override with the seed
        log (``otter.check.logs.Log``): an Otter log from which to deserialize environments to grade
            questions
        variables (``dict[str, str] | None``): map of variable names -> type string to use for type
            checking values deserialized from ``log``
        plugin_collection (``otter.plugins.PluginCollection | None``): a set of plugins to run the
            ``before_execution`` and ``after_grading`` events on this submission

    Returns:
        ``otter.test_files.GradingResults``: the results of grading
    """
    from nbconvert.preprocessors import ExecutePreprocessor

    from .preprocessor import GradingPreprocessor

    if tests_glob is None:
        tests_glob = []

    if not script:
        nb = nbformat.read(submission_path, as_version=NBFORMAT_VERSION)

    else:
        with open(submission_path) as f:
            nb = f.read()

        nb = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(nb)])

    if plugin_collection is not None:
        nb = plugin_collection.before_execution(nb)

    results_handle, results_file = tempfile.mkstemp(suffix=".pkl")

    try:
        c = Config()

        (host, port), stop_server = start_server()

        try:
            # GradingPreprocessor config
            c.GradingPreprocessor.cwd = cwd
            c.GradingPreprocessor.test_dir = test_dir
            c.GradingPreprocessor.tests_glob = tests_glob
            c.GradingPreprocessor.results_path = results_file
            c.GradingPreprocessor.seed = seed
            c.GradingPreprocessor.seed_variable = seed_variable
            c.GradingPreprocessor.otter_log = log
            c.GradingPreprocessor.variables = variables
            c.GradingPreprocessor.logging_server_host = host
            c.GradingPreprocessor.logging_server_port = port
            c.GradingPreprocessor.force_python3_kernel = force_python3_kernel

            # ExecutePreprocessor config
            c.ExecutePreprocessor.allow_errors = ignore_errors

            gp = GradingPreprocessor(config=c)
            ep = ExecutePreprocessor(config=c)

            nb, _ = gp.preprocess(nb)
            executed_nb, _ = ep.preprocess(nb)

        finally:
            stop_server()
            gp.cleanup()

        os.close(results_handle)

        try:
            with open(results_file, "rb") as f:
                results = pickle.load(f)
        except Exception as e:
            results = GradingResults.without_results(e)

        if not isinstance(results, GradingResults):
            raise TypeError(
                "Results deserialized from grading notebook were not a GradingResults instance"
            )

        results.notebook = executed_nb

        if plugin_collection is not None:
            plugin_collection.run("after_grading", results)

        return results

    finally:
        os.remove(results_file)


if TYPE_CHECKING:
    from ..check.logs import Log
