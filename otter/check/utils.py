"""Utilities for Otter Check"""

import nbformat as nbf
import os
import requests
import sys
import tempfile
import time
import wrapt

from enum import Enum
from glob import glob
from IPython import get_ipython
from IPython.display import display, Javascript
from subprocess import run, PIPE

from .logs import EventType

from ..utils import import_or_raise, NBFORMAT_VERSION, NOTEBOOK_METADATA_KEY


def save_notebook(filename, timeout=10):
    """
    Force-saves a Jupyter notebook by displaying JavaScript.

    Args:
        filename (``str``): path to notebook file being saved
        timeout (``int`` or ``float``): number of seconds to wait for save before timing-out

    Returns
        ``bool``: whether the notebook was saved successfully
    """
    if get_ipython() is not None:
        orig_mod_time = os.path.getmtime(filename)
        start = time.time()
        display(Javascript("""
            if (typeof Jupyter !== 'undefined') {
                Jupyter.notebook.save_checkpoint();
            }
            else {
                document.querySelector('[data-command="docmanager:save"]').click();
            }
        """))

        while time.time() - start < timeout:
            curr_mod_time = os.path.getmtime(filename)
            if orig_mod_time < curr_mod_time and os.path.getsize(filename) > 0:
                return True

            time.sleep(0.2)

        return False

    return True


def grade_zip_file(zip_path, nb_arcname, tests_dir):
    """
    Grade a submission zip file in a separate process and return the ``GradingResults`` object.
    """
    dill = import_or_raise("dill")

    results_handle, results_path = tempfile.mkstemp(suffix=".pkl")

    try:
        command = [
            sys.executable, "-m", "otter.check.validate_export",
            "--zip-path", zip_path,
            "--nb-arcname", nb_arcname,
            "--tests-dir", tests_dir,
            "--results-path", results_path,
        ]

        # run the command
        results = run(command, stdout=PIPE, stderr=PIPE)

        # TODO: remove
        print(results.stdout.decode("utf-8"))
        print(results.stderr.decode("utf-8"))

        if results.stderr:
            raise RuntimeError(results.stderr)

        with open(results_path, "rb") as f:
            results = dill.load(f)

        return results

    finally:
        os.close(results_handle)
        os.remove(results_path)


class IPythonInterpreter(Enum):
    """
    An enum of different types of IPython interpreters.
    """

    class Interpreter:
        """
        A class representing a flavor of IPython interpreter.

        Contains attributes for an importable name substring (used to check which interpreter is
        running) and a display name for error messages and the like.
        """

        def __init__(self, check_strs, display_name):
            self.check_strs = check_strs
            self.display_name = display_name

        def running(self):
            """
            Determine whether this interpreter is currently running by checking the string
            representation of the return value of ``IPython.get_ipython``.

            Returns:
                ``bool``: whether this interpreter is running
            """
            ipython_interp = str(get_ipython())
            return any(c in ipython_interp for c in self.check_strs)

    COLAB = Interpreter(["google.colab"], "Google Colab")
    """the Google Colab interpreter"""

    PYOLITE = Interpreter(["pyolite.", "pyodide_kernel."], "Jupyterlite")
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
                raise RuntimeError(f"This method is not compatible with {interpreter.value.display_name}")
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


def list_test_files(tests_dir):
    """
    Find all of the test files in the specified directory (that is, all ``.py`` files that are not
    named ``__init__.py``) and return their paths in a sorted list.

    Args:
        tests_dir (``str``): the path to the tests directory

    Returns:
        ``list[str]``: the sorted list of all test file paths in ``tests_dir``
    """
    return sorted([file for file in glob(os.path.join(tests_dir, "*.py")) \
            if file != "__init__.py"])


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
        tests = map(get_stem, list_test_files(tests_dir))

    else:
        if nb_path is None:
            raise ValueError("Tests directory does not exist and no notebook path provided")

        nb = nbf.read(nb_path, as_version=NBFORMAT_VERSION)
        tests = list(nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"].keys())

    return sorted(tests)


def resolve_test_info(tests_dir, nb_path, tests_url_prefix, question):
    """
    Determine the test path and test name.

    If ``tests_url_prefix`` is specified, the test file is downloaded from the URL
    ``{tests_url_prefix}/{question}.py`` and saved to the file ``{tests_dir}/{question}.py``. If
    ``tests_dir`` does not already exist, it is created.

    Args:
        tests_dir (``str``): the path to the directory of tests
        nb_path (``str``): the path to the notebook
        tests_url_prefix (``str | None``): the prefix of a URL to the test file
        question (``str``): the question name

    Returns:
        ``tuple[str, str]``: the test path and test name
    """
    if tests_url_prefix is not None:
        if not IPythonInterpreter.PYOLITE.value.running():
            raise ValueError("Downloading test files from URLs is only supported on JupyterLite")

        pyodide = import_or_raise("pyodide")

        test_url = f"{tests_url_prefix}{'/' if not tests_url_prefix.endswith('/') else ''}{question}.py"
        text = pyodide.open_url(test_url).getvalue()

        os.makedirs(tests_dir, exist_ok=True)

        test_path = os.path.join(tests_dir, f"{question}.py")
        test_name = None

        with open(test_path, "w+") as f:
            f.write(text)

    elif tests_dir and os.path.isdir(tests_dir):
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
