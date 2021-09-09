"""Utilities for Otter Check"""

import dill
import hashlib
import json
import os
import tempfile
import time

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
            results = dill.load(f)

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


def list_available_tests(tests_dir, nb_path):
    """
    Get a list of available questions by searching the tests directory (if present) or the notebook
    metadata.

    Args:
        tests_dir (``str``): the path to the tests directory
        nb_path (``str``): the path to the notebook

    Returns:
        ``list[str]``: the list of question names
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

    return tests


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
