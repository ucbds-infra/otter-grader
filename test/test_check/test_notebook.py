"""Tests for ``otter.Notebook``"""

import datetime as dt
import nbformat as nbf
import os
import pytest
import shutil

from glob import glob
from textwrap import dedent
from unittest import mock

from otter import Notebook
from otter.check.notebook import _OTTER_LOG_FILENAME, _ZIP_NAME_FILENAME
from otter.utils import (
    NO_PDF_EXPORT_MESSAGE_KEY,
    NOTEBOOK_METADATA_KEY,
    REQUIRE_CONFIRMATION_NO_PDF_EXPORT_KEY,
)

from ..utils import delete_paths, TestFileManager


FILE_MANAGER = TestFileManager(__file__)
TESTS_DIR = FILE_MANAGER.get_path("tests")
TESTS_GLOB = glob(FILE_MANAGER.get_path("tests/*.py"))
NB_PATH = FILE_MANAGER.get_path("subm.ipynb")
NB_PATH_STEM = os.path.splitext(os.path.basename(NB_PATH))[0]


def square(x):
    return x ** 2


def negate(x):
    return not x


@pytest.fixture(autouse=True)
def cleanup_output(cleanup_enabled):
    yield
    if cleanup_enabled:
        delete_paths([_OTTER_LOG_FILENAME])


@pytest.fixture
def write_notebook(cleanup_enabled):
    yield lambda nb: nbf.write(nb, NB_PATH)
    if cleanup_enabled:
        delete_paths([NB_PATH])


def test_check():
    """
    Checks that the cor checking behavior of ``otter.Notebook.check`` works correctly.
    """
    grader = Notebook(tests_dir=TESTS_DIR)

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


@mock.patch("otter.check.notebook.dt")
@mock.patch("otter.check.notebook.zipfile.ZipFile")
@mock.patch("otter.check.notebook.export_notebook")
def test_export(mocked_export, mocked_zf, mocked_dt, write_notebook):
    """
    Checks export contents for existence of PDF and equality of zip
    """
    write_notebook(nbf.v4.new_notebook())

    timestmap = dt.datetime(2022, 1, 3, 12, 12, 12, 1212)
    grader = Notebook(tests_dir=TESTS_DIR)

    with mock.patch.object(grader, "_resolve_nb_path") as mocked_resolve:
        mocked_resolve.return_value = NB_PATH
        mocked_dt.datetime.now.return_value = timestmap

        grader.export()

        zip_name = FILE_MANAGER.get_path(
            f"{NB_PATH_STEM}_{timestmap.strftime('%Y_%m_%dT%H_%M_%S_%f')}.zip")
        mocked_zf.assert_called_once_with(zip_name, mode="w")
        mocked_zf.return_value.write.assert_any_call(mocked_resolve.return_value)
        mocked_zf.return_value.write.assert_any_call(_OTTER_LOG_FILENAME)
        mocked_export.assert_called_once_with(NB_PATH, filtering=True, pagebreaks=True)
        mocked_zf.return_value.writestr.assert_called_with(_ZIP_NAME_FILENAME, os.path.basename(zip_name))


@mock.patch("otter.check.notebook.zipfile.ZipFile")
def test_export_with_directory_in_files(mocked_zf, write_notebook):
    """
    Checks that ``Notebook.export`` correctly recurses into subdirectories to find files when a
    directory is in the list passed to the ``files`` argument.
    """
    write_notebook(nbf.v4.new_notebook())

    file_path = FILE_MANAGER.get_path("data/foo.csv")
    dir_path = os.path.split(file_path)[0]
    os.makedirs(dir_path, exist_ok=True)
    with open(file_path, "w+") as f:
        f.write("hi there")

    try:
        grader = Notebook(tests_dir=TESTS_DIR)
        with mock.patch.object(grader, "_resolve_nb_path") as mocked_resolve:
            mocked_resolve.return_value = NB_PATH

            grader.export(pdf=False, files=[dir_path])

            mocked_zf.return_value.write.assert_any_call(file_path)

    finally:
        shutil.rmtree(dir_path)


@mock.patch("otter.check.utils.Button")
@mock.patch("otter.check.utils.HTML")
@mock.patch("otter.check.utils.Output")
@mock.patch("otter.check.utils.VBox")
@mock.patch("otter.check.utils.display")
@mock.patch("otter.check.notebook.dt")
@mock.patch("otter.check.notebook.zipfile.ZipFile")
@mock.patch("otter.check.notebook.export_notebook")
def test_export_with_no_pdf_ack(
    mocked_export,
    mocked_zf,
    mocked_dt,
    mocked_ipy_display,
    mocked_ipyw_vbox,
    mocked_ipyw_output,
    mocked_ipyw_html,
    mocked_ipyw_button,
    write_notebook,
):
    """
    Checks that ``Notebook.export`` works with a no PDF ACK configured.
    """
    nb = nbf.v4.new_notebook()
    nb.metadata[NOTEBOOK_METADATA_KEY] = {
        REQUIRE_CONFIRMATION_NO_PDF_EXPORT_KEY: True,
        NO_PDF_EXPORT_MESSAGE_KEY: "no pdf",
    }
    write_notebook(nb)

    timestmap = dt.datetime(2022, 1, 3, 12, 12, 12, 1212)
    grader = Notebook(NB_PATH)

    # with mock.patch.object(grader, "_resolve_nb_path") as mocked_resolve:
        # mocked_resolve.return_value = NB_PATH
    mocked_dt.datetime.now.return_value = timestmap
    mocked_export.return_value = FILE_MANAGER.get_path(f"{NB_PATH_STEM}.pdf")

    with pytest.warns(UserWarning, match="Could not locate a PDF to include"):
        grader.export()

    mocked_export.assert_called_with(NB_PATH, filtering=True, pagebreaks=True)

    mocked_ipyw_output.assert_called()
    mocked_ipyw_html.assert_any_call("""<p style="margin: 0">no pdf</p>""")
    mocked_ipyw_button.assert_called_with(description="Continue export", button_style="warning")
    mocked_ipyw_button.return_value.on_click.assert_called()
    mocked_ipyw_vbox.assert_called_with([
        mocked_ipyw_html.return_value,
        mocked_ipyw_button.return_value,
        mocked_ipyw_html.return_value,
        mocked_ipyw_output.return_value,
    ])
    mocked_ipy_display.assert_called_with(mocked_ipyw_vbox.return_value)

    mocked_ipyw_button.return_value.on_click.call_args.args[0]()

    zip_name = FILE_MANAGER.get_path(
        f"{NB_PATH_STEM}_{timestmap.strftime('%Y_%m_%dT%H_%M_%S_%f')}.zip")
    mocked_zf.assert_called_once_with(zip_name, mode="w")
    # mocked_zf.return_value.write.assert_any_call(mocked_resolve.return_value)
    mocked_zf.return_value.write.assert_any_call(NB_PATH)
    mocked_zf.return_value.write.assert_any_call(_OTTER_LOG_FILENAME)
    mocked_zf.return_value.writestr.assert_called_with(_ZIP_NAME_FILENAME, os.path.basename(zip_name))


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


@mock.patch("otter.check.notebook.Checker")
@mock.patch("otter.check.notebook.resolve_test_info")
@mock.patch.object(Notebook, "_resolve_nb_path")
def test_grading_mode(mocked_resolve_nb_path, mocked_resolve_test_info, _):
    """
    Check that a call to a grading-mode-disabled method is not executed.
    """
    mocked_resolve_nb_path.return_value = None
    mocked_resolve_test_info.return_value = ("", None)
    Notebook.init_grading_mode(tests_dir="foo")

    grader = Notebook(tests_dir=TESTS_DIR)

    # check will try to raise a FileNotFoundError because the test file doesn't exist; this is safe
    # to ignore since it's thrown after the call to resolve_test_info
    try: grader.check("q1")
    except FileNotFoundError: pass
    mocked_resolve_test_info.assert_called_once_with("foo", None, None, "q1")

    mocked_resolve_nb_path.reset_mock()

    grader.export()
    # if export is called, this method would be called first
    mocked_resolve_nb_path.assert_not_called()
