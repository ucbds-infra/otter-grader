"""Tests for ``otter.run``"""

import copy
import json
import nbformat
import nbconvert
import os
import pytest
import re

from contextlib import contextmanager, nullcontext
from unittest import mock

from otter.run.run_autograder import main as run_autograder
from otter.run.run_autograder.utils import OtterRuntimeError
from otter.utils import NBFORMAT_VERSION

from .utils import delete_paths, TestFileManager


FILE_MANAGER = TestFileManager("test/test-run")


@pytest.fixture(autouse=True)
def cleanup_output(cleanup_enabled):
    yield
    if cleanup_enabled:
        delete_paths([
            FILE_MANAGER.get_path("autograder/results/results.json"),
            FILE_MANAGER.get_path("autograder/results/results.pkl"),
            FILE_MANAGER.get_path("autograder/__init__.py"),
            FILE_MANAGER.get_path("autograder/submission/test"),
            FILE_MANAGER.get_path("autograder/submission/tests"),
            FILE_MANAGER.get_path("autograder/submission/__init__.py"),
            FILE_MANAGER.get_path("autograder/submission/.OTTER_LOG"),
            FILE_MANAGER.get_path("rmd-autograder/results/results.json"),
            FILE_MANAGER.get_path("rmd-autograder/results/results.pkl"),
            FILE_MANAGER.get_path("rmd-autograder/__init__.py"),
            FILE_MANAGER.get_path("rmd-autograder/submission/test"),
            FILE_MANAGER.get_path("rmd-autograder/submission/tests"),
            FILE_MANAGER.get_path("rmd-autograder/submission/__init__.py"),
            FILE_MANAGER.get_path("rmd-autograder/submission/.OTTER_LOG"),
        ])


@pytest.fixture(autouse=True)
def correct_cwd_on_exit():
    cwd = os.getcwd()
    yield
    os.chdir(cwd)


@pytest.fixture
def expected_results():
    return {
        "tests": [
            {
                "name": "Public Tests",
                "visibility": "visible",
                "output": "q1 results: All test cases passed!\n\nq2 results:\n    q2 - 1 result:\n        ❌ Test case failed\n        Trying:\n            negate(True)\n        Expecting:\n            False\n        **********************************************************************\n        Line 2, in q2 0\n        Failed example:\n            negate(True)\n        Expected:\n            False\n        Got:\n            True\n\n    q2 - 2 result:\n        ❌ Test case failed\n        Trying:\n            negate(False)\n        Expecting:\n            True\n        **********************************************************************\n        Line 2, in q2 1\n        Failed example:\n            negate(False)\n        Expected:\n            True\n        Got:\n            False\n\nq3 results: All test cases passed!\n\nq4 results: All test cases passed!\n\nq6 results: All test cases passed!\n\nq7 results: All test cases passed!",
                "status": "failed",
            },
            {
                "name": "q1",
                "score": 0.0,
                "max_score": 0.0,
                "visibility": "hidden",
                "output": "q1 results: All test cases passed!"
            },
            {
                "name": "q2",
                "score": 0,
                "max_score": 2.0,
                "visibility": "hidden",
                "output": "q2 results:\n    q2 - 1 result:\n        ❌ Test case failed\n        Trying:\n            negate(True)\n        Expecting:\n            False\n        **********************************************************************\n        Line 2, in q2 0\n        Failed example:\n            negate(True)\n        Expected:\n            False\n        Got:\n            True\n\n    q2 - 2 result:\n        ❌ Test case failed\n        Trying:\n            negate(False)\n        Expecting:\n            True\n        **********************************************************************\n        Line 2, in q2 1\n        Failed example:\n            negate(False)\n        Expected:\n            True\n        Got:\n            False\n\n    q2 - 3 result:\n        ❌ Test case failed\n        Trying:\n            negate(\"\")\n        Expecting:\n            True\n        **********************************************************************\n        Line 2, in q2 2\n        Failed example:\n            negate(\"\")\n        Expected:\n            True\n        Got:\n            ''\n\n    q2 - 4 result:\n        ❌ Test case failed\n        Trying:\n            negate(1)\n        Expecting:\n            False\n        **********************************************************************\n        Line 2, in q2 3\n        Failed example:\n            negate(1)\n        Expected:\n            False\n        Got:\n            1"
            },
            {
                "name": "q3",
                "score": 2.0,
                "max_score": 2.0,
                "visibility": "hidden",
                "output": "q3 results: All test cases passed!"
            },
            {
                "name": "q4",
                "score": 1.0,
                "max_score": 1.0,
                "visibility": "hidden",
                "output": "q4 results: All test cases passed!"
            },
            {
                "name": "q6",
                "score": 2.5,
                "max_score": 5.0,
                "visibility": "hidden",
                "output": "q6 results:\n    q6 - 1 result:\n        ✅ Test case passed\n\n    q6 - 2 result:\n        ❌ Test case failed\n        Trying:\n            fib = fiberator()\n        Expecting nothing\n        ok\n        Trying:\n            for _ in range(10):\n                print(next(fib))\n        Expecting:\n            0\n            1\n            1\n            2\n            3\n            5\n            8\n            13\n            21\n            34\n        **********************************************************************\n        Line 3, in q6 1\n        Failed example:\n            for _ in range(10):\n                print(next(fib))\n        Expected:\n            0\n            1\n            1\n            2\n            3\n            5\n            8\n            13\n            21\n            34\n        Got:\n            0\n            1\n            1\n            1\n            2\n            3\n            5\n            8\n            13\n            21"
            },
            {
                "name": "q7",
                "score": 1.0,
                "max_score": 1.0,
                "visibility": "hidden",
                "output": "q7 results: All test cases passed!"
            }
        ],
        "output": "Students are allowed 1 submissions every 1 days. You have 0 submissions in that period.",
    }


@pytest.fixture(scope="module")
def expected_rmd_results():
    return {
        "tests": [
            {
                "name": "Public Tests",
                "output": "q1 results: All test cases passed!",
                "visibility": "visible",
                "status": "passed",
            },
            {
                "max_score": 5,
                "name": "q1",
                "output": "q1 results: All test cases passed!\nq1d message: congrats",
                "score": 5,
                "visibility": "hidden",
            },
        ],
    }


@contextmanager
def alternate_config(config_path, new_config):
    with open(config_path) as f:
        contents = f.read()
    with open(config_path, "w") as f:
        json.dump(new_config, f)
    yield
    with open(config_path, "w") as f:
        f.write(contents)


def get_expected_error_results(error):
    return {
        "score": 0,
        "stdout_visibility": "hidden",
        "tests": [
            {
                "name": "Autograder Error",
                "output": f"Otter encountered an error when grading this submission:\n\n{error}",
            },
        ],
    }


@pytest.fixture
def get_config_path():
    def do_get_config_path(rmd=False):
        dirname = "autograder" if not rmd else "rmd-autograder"
        return FILE_MANAGER.get_path(f"{dirname}/source/otter_config.json")
    return do_get_config_path


@pytest.fixture
def load_config(get_config_path):
    def load_config_file(rmd=False):
        with open(get_config_path(rmd=rmd)) as f:
            return json.load(f)
    return load_config_file


def test_notebook(load_config, expected_results):
    config = load_config()
    run_autograder(config['autograder_dir'])

    with FILE_MANAGER.open("autograder/results/results.json") as f:
        actual_results = json.load(f)

    assert actual_results == expected_results, \
        f"Actual results did not matched expected:\n{actual_results}"


def test_pdf_generation_failure(get_config_path, load_config, expected_results):
    config = load_config()
    config["warn_missing_pdf"] = True
    config["token"] = "abc123"

    expected_results["tests"].insert(1, {
        "name": "PDF Generation Failed",
        "visibility": "visible",
        "output": "nu-uh",
        "status": "failed",
    })

    with alternate_config(get_config_path(), config):
        with mock.patch("otter.run.run_autograder.runners.python_runner.export_notebook") as \
                mocked_export:
            mocked_export.side_effect = ValueError("nu-uh")
            run_autograder(config['autograder_dir'])

    with FILE_MANAGER.open("autograder/results/results.json") as f:
        actual_results = json.load(f)

    assert actual_results == expected_results, \
        f"Actual results did not matched expected:\n{actual_results}"


def test_force_public_test_summary(get_config_path, load_config):
    config = load_config()

    def perform_test(show_hidden, force_public_test_summary, expect_summary):
        config["show_hidden"] = show_hidden
        config["force_public_test_summary"] = force_public_test_summary
        with alternate_config(get_config_path(), config):
            run_autograder(config['autograder_dir'])

        with FILE_MANAGER.open("autograder/results/results.json") as f:
            actual_results = json.load(f)

        message = f"show_hidden={show_hidden}, force_public_test_summary={force_public_test_summary}, expect_summary={expect_summary}"
        if expect_summary:
            assert actual_results["tests"][0]["name"] == "Public Tests", message
        else:
            assert actual_results["tests"][0]["name"] != "Public Tests", message

    perform_test(False, False, True)
    perform_test(False, True, True)
    perform_test(True, False, False)
    perform_test(True, True, True)


def test_script(load_config, expected_results):
    config = load_config()
    nb_path = FILE_MANAGER.get_path("autograder/submission/fails2and6H.ipynb")
    nb = nbformat.read(nb_path, as_version=NBFORMAT_VERSION)
    os.remove(nb_path)

    try:
        py, _ = nbconvert.export(nbconvert.PythonExporter, nb)

        # remove magic commands
        py = "\n".join(l for l in py.split("\n") if not l.startswith("get_ipython"))

        with FILE_MANAGER.open("autograder/submission/fails2and6H.py", "w+") as f:
            f.write(py)

        run_autograder(config['autograder_dir'])

        with FILE_MANAGER.open("autograder/results/results.json") as f:
            actual_results = json.load(f)

        assert actual_results == expected_results, \
            f"Actual results did not matched expected:\n{actual_results}"

    finally:
        delete_paths([FILE_MANAGER.get_path("autograder/submission/fails2and6H.py")])
        with open(nb_path, "w+") as f:
            nbformat.write(nb, f)


def test_assignment_name(load_config, expected_results):
    name = "hw01"
    config = load_config()
    nb_path = FILE_MANAGER.get_path("autograder/submission/fails2and6H.ipynb")
    orig_nb = nbformat.read(nb_path, as_version=NBFORMAT_VERSION)
    nb = copy.deepcopy(orig_nb)

    def perform_test(nb, expected_results, error=None, **kwargs):
        nbformat.write(nb, nb_path)

        cm = pytest.raises(OtterRuntimeError, match=re.escape(error)) if error is not None \
            else nullcontext()
        with cm:
            run_autograder(config["autograder_dir"], assignment_name = name, **kwargs)

        with FILE_MANAGER.open("autograder/results/results.json") as f:
            actual_results = json.load(f)

        assert actual_results == expected_results, \
            f"Actual results did not matched expected:\n{actual_results}"

    error_message_template = "Received submission for assignment '{got}' (this is assignment " \
            "'{want}')"

    try:
        # test with correct name
        nb["metadata"]["otter"] = {"assignment_name": name}
        perform_test(nb, expected_results)

        # test with wrong name
        bad_name = "lab01"
        error_message = error_message_template.format(got=bad_name, want=name)
        nb["metadata"]["otter"]["assignment_name"] = bad_name
        perform_test(nb, get_expected_error_results(error_message), error=error_message)

        # test with no name in nb
        error_message = error_message_template.format(got=None, want=name)
        nb["metadata"]["otter"].pop("assignment_name")
        perform_test(nb, get_expected_error_results(error_message), error=error_message)

    finally:
        delete_paths([nb_path])
        with open(nb_path, "w+") as f:
            nbformat.write(nb, f)


def test_rmd(load_config, expected_rmd_results):
    name = "hw01"
    config = load_config(True)
    rmd_path = FILE_MANAGER.get_path("rmd-autograder/submission/hw01.Rmd")
    with open(rmd_path) as f:
        orig_rmd = f.read()

    sub_name = lambda n: re.sub(r"assignment_name: \"\w+\"", f"assignment_name: \"{n}\"", orig_rmd)

    def perform_test(rmd, expected_results, error=None, **kwargs):
        with open(rmd_path, "w") as f:
            f.write(rmd)

        cm = pytest.raises(OtterRuntimeError, match=re.escape(error)) if error is not None \
            else nullcontext()
        with cm:
            run_autograder(config["autograder_dir"], assignment_name = name, **kwargs)

        with FILE_MANAGER.open("rmd-autograder/results/results.json") as f:
            actual_results = json.load(f)

        assert actual_results == expected_results, \
            f"Actual results did not matched expected:\n{actual_results}"

    error_message_template = "Received submission for assignment '{got}' (this is assignment " \
            "'{want}')"

    try:
        # test with correct name
        perform_test(orig_rmd, expected_rmd_results)

        # test with wrong name
        bad_name = "lab01"
        error_message = error_message_template.format(got=bad_name, want=name)
        perform_test(
            sub_name(bad_name), get_expected_error_results(error_message), error=error_message)

        # test with no name in Rmd
        error_message = error_message_template.format(got=None, want=name)
        perform_test(
            "\n".join([l for l in orig_rmd.split("\n") if not l.startswith("assignment_name: ")]),
            get_expected_error_results(error_message),
            error=error_message,
        )

    finally:
        delete_paths([rmd_path])
        with open(rmd_path, "w+") as f:
            f.write(orig_rmd)
