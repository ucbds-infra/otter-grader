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
