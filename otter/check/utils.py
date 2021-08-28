"""
Utils for Otter Check
"""

import hashlib
import os
import pickle
import tempfile
import time

from IPython import get_ipython
from IPython.display import display, Javascript
from subprocess import run, PIPE

from .logs import EventType


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
        f = open(filename, "rb")
        md5 = hashlib.md5(f.read()).hexdigest()
        start = time.time_ns()
        display(Javascript("Jupyter.notebook.save_checkpoint();"))
        
        curr = md5
        while curr == md5 and time.time_ns() - start <= timeout:
            time.sleep(1)
            f.seek(0)
            curr = hashlib.md5(f.read()).hexdigest()
        
        f.close()

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
            results = pickle.load(f)

        return results

    finally:
        os.remove(results_path)


def running_on_colab():
    """
    Determine whether the current environment is running on Google Colab by checking the IPython
    interpreter.

    Returns:
        ``bool``: whether the current environment is on Google Colab
    """
    return "google.colab" in str(get_ipython())


def colab_incompatible(f):
    """
    A decator that raises an error if the wrapped function is called in an environment running on
    Google Colab.
    """
    def colab_only_method(self, *args, **kwargs):
        if self._colab:
            raise RuntimeError("This method is not compatible with Google Colab")
        return f(self, *args, **kwargs)
    return colab_only_method


def logs_event(event_type):
        """
        A decorator that ensures each call is logged in the Otter log with type ``event_type``.

        Events logging a ``EventType.CHECK`` should return a 3-tuple of the question name, the
        ``TestFile`` and an environment to shelve. All other methods should just return their 
        default return value, which will be logged.
        """

        def event_logger(f):
            """
            Wraps a function and ensures that the call's results are logged using 
            ``Notebook._log_event``.
            """

            def run_function(self, *args, **kwargs):
                """
                Runs a method, catching any errors and logging the call. Returns the return value
                of the function, unless ``EventType.CHECK`` is used, in which case the return value
                is assumed to be a 3-tuple and the second value in the tuple is returned.
                """
                try:
                    if event_type == EventType.CHECK:
                        question, results, shelve_env = f(self, *args, **kwargs)
                    else:
                        results = f(self, *args, **kwargs)
                        shelve_env = {}
                        question = None
                except Exception as e:
                    self._log_event(event_type, success=False, error=e)
                    raise e
                else:
                    self._log_event(event_type, results=results, question=question, shelve_env=shelve_env)
                return results

            return run_function

        return event_logger
