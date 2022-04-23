"""Utilities for Otter Check"""

import dill
import hashlib
import json
import os
import tempfile
import time
import wrapt

from enum import Enum
from glob import glob
from IPython import get_ipython
from IPython.display import display, Javascript
from subprocess import run, PIPE

from .logs import EventType

from ..test_files import NOTEBOOK_METADATA_KEY


def save_notebook(filename, timeout=10):
    """
    Force-saves a Jupyter notebook by displaying JavaScript.

    Args:
        filename (``str``): path to notebook file being saved
        timeout (``int`` or ``float``): number of seconds to wait for save before timing-out

    Returns
        ``bool``: whether the notebook was saved successfully
    """
    timeout = timeout * 10**9
    if get_ipython() is not None:
        with open(filename, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        start = time.time_ns()
        display(Javascript("Jupyter.notebook.save_checkpoint();"))

        curr = md5
        while curr == md5 and time.time_ns() - start <= timeout:
            time.sleep(1)
            with open(filename, "rb") as f:
                curr = hashlib.md5(f.read()).hexdigest()


        return curr != md5

    return True


def grade_zip_file(zip_path, nb_arcname, tests_dir):
    """
    Grade a submission zip file in a separate process and return the ``GradingResults`` object.
    """
    _, results_path = tempfile.mkstemp(suffix=".pkl")

    try:
        command = [
            "python3", "-m", "otter.check.validate_export",
            "--zip-path", zip_path,
            "--nb-arcname", nb_arcname,
            "--tests-dir", tests_dir,
            "--results-path", results_path,
        ]

        # run the command
        results = run(command, stdout=PIPE, stderr=PIPE)

        if results.stderr:
            raise RuntimeError(results.stderr)

        with open(results_path, "rb") as f:
            results = dill.load(f)

        return results

    finally:
        os.remove(results_path)


class IPythonInterpreter(Enum):
    """
    An enum of different types of IPython interpreters.
    """

    class Interpreter:
        """
        """

        def __init__(self, check_str):
            self.check_str = check_str

        def running(self):
            """
            """
            return self.check_str in str(get_ipython())

    COLAB = Interpreter("google.colab")
    """the Google Colab interpreter"""

    PYOLITE = Interpreter("pyolite.")
    """the JupyterLite interpreter"""


def incompatible_with(interpreter, throw_error = True):
    """
    Create a decorator indicating that a method is incompatible with a specific interpreter.
    """
    @wrapt.decorator
    def incompatible(wrapped, self, args, kwargs):
        """
        A decorator that raises an error or performs no action (depending on ``throw_error``) if the
        wrapped function is called in an environment running on the specified interpreter.
        """
        if self._interpreter is interpreter:
            if throw_error:
                raise RuntimeError("This method is not compatible with Google Colab")
            else:
                return
        return wrapped(*args, **kwargs)

    return incompatible


@wrapt.decorator
def grading_mode_disabled(wrapped, self, args, kwargs):
    """
    A decorator that returns without calling the wrapped function if the ``Notebook`` grading mode
    is enabled.
    """
    if type(self)._grading_mode:
        return
    return wrapped(*args, **kwargs)


# TODO: use this class to replace tuple return values in logs_event
# class LoggedEventReturnValue:
#     def __init__(self, return_value, results=None, shelve_env=None):
#         self.return_value = return_value
#         self.results = results
#         self.shelve_env = shelve_env


def logs_event(event_type):
    """
    A decorator that ensures each call is logged in the Otter log with type ``event_type``.

    Events logging a ``EventType.CHECK`` should return a 3-tuple of the question name, the
    ``TestFile`` and an environment to shelve. All other methods should just return their 
    default return value, which will be logged.
    """
    @wrapt.decorator        
    def event_logger(wrapped, self, args, kwargs):
        """
        Runs a method, catching any errors and logging the call. Returns the return value
        of the function, unless ``EventType.CHECK`` is used, in which case the return value
        is assumed to be a 3-tuple and the second value in the tuple is returned.
        """
        try:
            if event_type == EventType.CHECK:
                question, results, shelve_env = wrapped(*args, **kwargs)

            else:
                results = wrapped(*args, **kwargs)
                shelve_env = {}
                question = None

        except Exception as e:
            self._log_event(event_type, success=False, error=e)
            raise e

        else:
            self._log_event(event_type, results=results, question=question, shelve_env=shelve_env)

        return results

    return event_logger


def list_available_tests(tests_dir, nb_path):
    """
    Get a list of available questions by searching the tests directory (if present) or the notebook
    metadata.

    Args:
        tests_dir (``str``): the path to the tests directory
        nb_path (``str``): the path to the notebook

    Returns:
        ``list[str]``: the sorted list of question names
    """
    get_stem = lambda p: os.path.splitext(os.path.basename(p))[0]

    if tests_dir and os.path.isdir(tests_dir):
        tests = [get_stem(file) for file in glob(os.path.join(tests_dir, "*.py")) \
            if file != "__init__.py"]

    else:
        if nb_path is None:
            raise ValueError("Tests directory does not exist and no notebook path provided")

        with open(nb_path) as f:
            nb = json.load(f)

        tests = list(nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"].keys())

    return sorted(tests)


def resolve_test_info(tests_dir, nb_path, question):
    """
    Determine the test path and test name.

    Args:
        tests_dir (``str``): the path to the directory of tests
        nb_path (``str``): the path to the notebook
        question (``str``): the question name

    Returns:
        ``tuple[str, str]``: the test path and test name
    """
    if tests_dir and os.path.isdir(tests_dir):
        if not os.path.isfile(os.path.join(tests_dir, question + ".py")):
            raise FileNotFoundError(f"Test {question} does not exist")

        test_path = os.path.join(tests_dir, question + ".py")
        test_name = None

    else:
        if nb_path is None:
            raise ValueError("Tests directory does not exist and no notebook path provided")

        test_path = nb_path
        test_name = question

    return test_path, test_name
