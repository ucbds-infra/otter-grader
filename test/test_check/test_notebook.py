"""Tests for ``otter.Notebook``"""

import datetime as dt
import os
import pytest

from glob import glob
from textwrap import dedent
from unittest import mock

from otter import Notebook
from otter.check.notebook import _OTTER_LOG_FILENAME, _ZIP_NAME_FILENAME

from ..utils import TestFileManager


FILE_MANAGER = TestFileManager(__file__)
TESTS_DIR = FILE_MANAGER.get_path("tests")
TESTS_GLOB = glob(FILE_MANAGER.get_path("tests/*.py"))


def square(x):
    return x ** 2


def negate(x):
    return not x


@pytest.fixture(autouse=True)
def cleanup_output(cleanup_enabled):  # TODO: refactor this and similar to use delete_paths
    yield
    if cleanup_enabled and os.path.isfile(_OTTER_LOG_FILENAME):
        os.remove(_OTTER_LOG_FILENAME)


def test_check():
    """
    Checks that the cor checking behavior of ``otter.Notebook.check`` works correctly.
    """
    grader = Notebook(tests_dir=TESTS_DIR)  # TODO: move to fixture?

    def square(x):
        return x ** 2

    def negate(x):
        return not x

    global_env = {
        "square": square,
        "negate": negate,
    }

    expected_reprs = {
        "q1": 'q1 results: All test cases passed!',
        "q2": dedent("""\
            q2 results:
                q2 - 1 result:
                    ❌ Test case failed
                    Trying:
                        1 == 1
                    Expecting:
                        False
                    **********************************************************************
                    Line 2, in q2 0
                    Failed example:
                        1 == 1
                    Expected:
                        False
                    Got:
                        True

                q2 - 2 result:
                    ✅ Test case passed
        """).strip(),
        "q3": 'q3 results: All test cases passed!',
        "q4": 'q4 results: All test cases passed!',
        "q5": 'q5 results: All test cases passed!',
    }

    for q_path in TESTS_GLOB:
        q = os.path.split(q_path)[1][:-3]
        result = grader.check(q, global_env=global_env)
        if q != "q2":
            assert result.grade == 1, "Test {} failed".format(q)
        else:
            assert result.grade == 0, "Test {} passed".format(q)

        assert repr(result) == expected_reprs[q]

        # check with no global_env
        result = grader.check(q)
        if q != "q2":
            assert result.grade == 1, "Test {} failed".format(q)
        else:
            assert result.grade == 0, "Test {} passed".format(q)


@mock.patch("otter.check.notebook.export_notebook")
def test_to_pdf_with_nb_path(mocked_export):
    """
    Checks for existence of notebook PDF
    This test is the general use case WITH a specified notebook path
    """
    nb_path = "foo.ipynb"
    grader = Notebook(tests_dir=TESTS_DIR)
    with mock.patch.object(grader, "_resolve_nb_path") as mocked_resolve:
        mocked_resolve.return_value = nb_path

        grader.to_pdf(filtering=False)
        mocked_export.assert_called_once_with(nb_path, filtering=False, pagebreaks=True)

        # TODO: test display_link


@mock.patch("otter.check.notebook.dt")
@mock.patch("otter.check.notebook.zipfile.ZipFile")
@mock.patch("otter.check.notebook.export_notebook")
def test_export(mocked_export, mocked_zf, mocked_dt):
    """
    Checks export contents for existence of PDF and equality of zip
    """
    timestmap = dt.datetime(2022, 1, 3, 12, 12, 12, 1212)
    grader = Notebook(tests_dir=TESTS_DIR)

    with mock.patch.object(grader, "_resolve_nb_path") as mocked_resolve, \
            mock.patch("builtins.open", mock.mock_open(read_data="{}")), \
            open(_OTTER_LOG_FILENAME, mode="wb+"):
        mocked_resolve.return_value = "foo.ipynb"
        mocked_dt.datetime.now.return_value = timestmap

        grader.export(pdf=False)

        zip_name = f"foo_{timestmap.strftime('%Y_%m_%dT%H_%M_%S_%f')}.zip"
        mocked_zf.assert_called_once_with(zip_name, mode="w")
        mocked_zf.return_value.write.assert_any_call(mocked_resolve.return_value)
        mocked_zf.return_value.write.assert_any_call(_OTTER_LOG_FILENAME)
        mocked_export.assert_not_called()
        mocked_zf.return_value.writestr.assert_called_with(_ZIP_NAME_FILENAME, zip_name)

    # TODO: test with pdf
    # TODO: test force_save
    # TODO: test run_tests
    # TODO: test display_link


@mock.patch("otter.check.notebook.os.path.isdir")
def test_colab(mocked_isdir):
    """
    Checks that the ``Notebook`` class correctly disables methods on Google Colab.
    """
    mocked_isdir.return_value = False
    with pytest.raises(ValueError, match=f"Tests directory {TESTS_DIR} does not exist"):
        grader = Notebook(tests_dir=TESTS_DIR, colab=True)

    mocked_isdir.assert_called_once_with(TESTS_DIR)

    mocked_isdir.return_value = True
    grader = Notebook(tests_dir=TESTS_DIR, colab=True)

    # check for appropriate errors
    with pytest.raises(RuntimeError, match="This method is not compatible with Google Colab"):
        grader.run_plugin()

    with pytest.raises(RuntimeError, match="This method is not compatible with Google Colab"):
        grader.to_pdf()

    with pytest.raises(RuntimeError, match="This method is not compatible with Google Colab"):
        grader.add_plugin_files()

    with pytest.raises(RuntimeError, match="This method is not compatible with Google Colab"):
        grader.export()


def test_jupyterlite():
    """
    Checks that the ``Notebook`` class correctly disables methods on Google Colab.
    """
    tests_url_prefix = "https://domain.tld/"
    grader = Notebook(tests_url_prefix=tests_url_prefix, jupyterlite=True)

    # check for appropriate errors
    with mock.patch("otter.check.notebook.LogEntry") as mocked_event:
        grader._log_event()
        mocked_event.assert_not_called()

    with mock.patch("otter.check.utils.import_or_raise") as mocked_import, \
            mock.patch("otter.check.utils.os") as mocked_os, \
            mock.patch("otter.check.utils.open", mock.mock_open()) as mocked_open, \
            mock.patch("otter.check.utils.IPythonInterpreter") as mocked_interp:
        mocked_interp.PYOLITE.value.running.return_value = True
        mocked_os.path.join.return_value = FILE_MANAGER.get_path("tests/q1.py")

        grader.check("q1")

        mocked_import.assert_called_with("pyodide")
        mocked_pyodide = mocked_import.return_value
        mocked_pyodide.open_url.assert_called_with(f"{tests_url_prefix}q1.py")
        mocked_os.makedirs.assert_called_with("./tests", exist_ok=True)
        mocked_open.assert_called_with(mocked_os.path.join.return_value, "w+")


@mock.patch.object(Notebook, "_resolve_nb_path")
def test_grading_mode(mocked_resolve):
    """
    Check that a call to a grading-mode-disabled method is not executed.
    """
    Notebook.init_grading_mode(tests_dir="foo")

    grader = Notebook(tests_dir=TESTS_DIR)
    grader.export()

    # TODO: find a better way of doing this than accessing a private field
    assert grader._path == "foo"

    # if export is called, this method would be called first
    mocked_resolve.assert_not_called()


# TODO: tests for force_save on export and to_pdf
# TODO: test _resolve_nb_path
# TODO: tests for event logging and other things in otter.check.utils
