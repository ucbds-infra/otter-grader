"""Tests for ``otter.assign``"""

import nbformat as nbf
import os
import pytest
import shutil

from glob import glob
from unittest import mock

from otter.assign import main as assign
from otter.assign.assignment import Assignment
from otter.assign.question_config import QuestionConfig
from otter.assign.tests_manager import AssignmentTestsManager, TestCase
from otter.generate.token import APIClient
from otter.utils import dump_yaml

from ..utils import assert_dirs_equal, TestFileManager, unzip_to_temp


# prevent pytest from thinking TestCase is a testing class
TestCase.__test__ = False


FILE_MANAGER = TestFileManager(__file__)


@pytest.fixture(autouse=True)
def cleanup_output(cleanup_enabled):
    """
    Removes assign output
    """
    yield
    if cleanup_enabled and os.path.exists(FILE_MANAGER.get_path("output")):
        shutil.rmtree(FILE_MANAGER.get_path("output"))


def check_gradescope_zipfile(path, correct_dir_path):
    """
    Checks that the autograder zip file at ``path`` matches ``correct_dir_path``.
    """
    with unzip_to_temp(path) as unzipped_dir:
        assert_dirs_equal(unzipped_dir, correct_dir_path)


def assign_and_check_output(nb_path, correct_dir, assign_kwargs={}, assert_dirs_equal_kwargs={}):
    """
    Runs Otter Assign and verifies that the output directories are correct.
    """
    output_path = FILE_MANAGER.get_path("output")
    assign(nb_path, output_path, **assign_kwargs)
    assert_dirs_equal(output_path, correct_dir, **assert_dirs_equal_kwargs)


# TODO: refactor existing tests to use this
@pytest.fixture
def generate_master_notebook(cleanup_enabled):
    """
    Yields a function that generates a master notebook file with a specific assignment config and
    returns the path at which the notebook was written. This fixture also deletes the notebook file
    during cleanup.
    """
    nb_path = FILE_MANAGER.get_path("master.ipynb")

    def generate_notebook(assignment_config):
        if os.path.exists(nb_path):
            raise RuntimeError(f"{nb_path} already exists")
        nb = nbf.read(FILE_MANAGER.get_path("master-skeleton.ipynb"), as_version=nbf.NO_CONVERT)
        config_cell = nbf.v4.new_raw_cell("# ASSIGNMENT CONFIG\n" + dump_yaml(assignment_config))
        nb.cells.insert(0, config_cell)

        nbf.write(nb, nb_path)

        return nb_path

    yield generate_notebook

    if cleanup_enabled:
        os.remove(nb_path)


def test_convert_example():
    """
    Checks that otter assign filters and outputs correctly
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("example.ipynb"), 
        FILE_MANAGER.get_path("example-correct"), 
        assign_kwargs=dict(no_run_tests=True),
        assert_dirs_equal_kwargs=dict(variable_path_exts=[".zip"]),
    )

    # check gradescope zip file
    check_gradescope_zipfile(
        glob(FILE_MANAGER.get_path("output/autograder/*.zip"))[0], 
        FILE_MANAGER.get_path("example-autograder-correct"),
    )


def test_exception_example():
    """
    Checks that otter assign filters and outputs correctly
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("exception-example.ipynb"), 
        FILE_MANAGER.get_path("exception-correct"), 
        assign_kwargs=dict(no_run_tests=True),
        assert_dirs_equal_kwargs=dict(variable_path_exts=[".zip"]),
    )


def test_otter_example():
    """
    Checks that otter assign filters and outputs correctly, as well as creates a correct .otter file
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("generate-otter.ipynb"), 
        FILE_MANAGER.get_path("otter-correct"),
        assert_dirs_equal_kwargs=dict(variable_path_exts=[".zip"]),
    )


def test_pdf_example():
    """
    Checks that otter assign filters and outputs correctly, as well as creates a correct .zip file
    along with PDFs
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("generate-pdf.ipynb"),
        FILE_MANAGER.get_path("pdf-correct"),
        assign_kwargs=dict(no_run_tests=True),
        assert_dirs_equal_kwargs=dict(ignore_ext=[".pdf"], variable_path_exts=[".zip"]),
    )


@mock.patch.object(APIClient, "get_token")
def test_gradescope_example(mocked_client):
    """
    Checks that otter assign filters and outputs correctly, as well as creates a correct .zip file
    along with PDFs. Additionally, includes testing Gradescope integration.
    """
    # set a return value that does not match the token in the notebook, so we'll know if APIClient
    # is called
    mocked_client.return_value = 'token'

    assign_and_check_output(
        FILE_MANAGER.get_path("generate-gradescope.ipynb"),
        FILE_MANAGER.get_path("gs-correct"),
        assign_kwargs=dict(no_run_tests=True),
        assert_dirs_equal_kwargs=dict(ignore_ext=[".pdf"], variable_path_exts=[".zip"]),
    )

    # check gradescope zip file
    check_gradescope_zipfile(
        glob(FILE_MANAGER.get_path("output/autograder/*.zip"))[0], 
        FILE_MANAGER.get_path("gs-autograder-correct"),
    )


def test_r_example():
    """
    Checks that otter assign works for R notebooks correctly
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("r-example.ipynb"),
        FILE_MANAGER.get_path("r-correct"),
        assert_dirs_equal_kwargs=dict(ignore_ext=[".pdf"], variable_path_exts=[".zip"]),
    )


def test_rmd_example():
    """
    Checks that otter assign works for Rmd files
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("rmd-example.Rmd"),
        FILE_MANAGER.get_path("rmd-correct"),
        assert_dirs_equal_kwargs=dict(
            ignore_ext=[".pdf"],
            ignore_dirs=["rmd-example-sol_files"],
            variable_path_exts=[".zip"],
        ),
    )

    # check gradescope zip file
    check_gradescope_zipfile(
        glob(FILE_MANAGER.get_path("output/autograder/*.zip"))[0], 
        FILE_MANAGER.get_path("rmd-autograder-correct"),
    )


def test_point_value_rounding():
    """
    Tests that point values are rounded appropriately.
    """
    question = QuestionConfig({"name": "q1", "points": None, "manual": False})
    tests_mgr = AssignmentTestsManager(Assignment())
    for _ in range(11):
        tests_mgr._add_test_case(question, TestCase("", "", False, 4 / 11, "", ""))

    # sum(4 / 11 for _ in range(11)) evaluates to 4.000000000000001 in Python, so this will
    # check that the per-test-case point values are correctly rounded.
    points = tests_mgr.determine_question_point_value(question)
    assert points == 4


def test_determine_question_point_value_error_message():
    """
    Tests that error messages for point value validations contain the question name.
    """
    question = QuestionConfig({"name": "q1", "points": 1, "manual": False})
    tests_mgr = AssignmentTestsManager(Assignment())
    for _ in range(2):
        tests_mgr._add_test_case(question, TestCase("", "", False, 1, "", ""))

    exception = None
    try:
        tests_mgr.determine_question_point_value(question)
    except Exception as e:
        exception = e

    assert str(exception) == "Error in \"q1\" test cases: More points specified in test cases " \
        "than allowed for test"
    assert type(exception) == ValueError


def test_jupyterlite(generate_master_notebook):
    """
    Tests that Otter Assign produces correct notebooks for running on Jupyterlite.
    """
    master_nb_path = generate_master_notebook({
        "runs_on": "jupyterlite",
        "tests": {"url_prefix": "https://domain.tld/tests/"}
    })
    assign_and_check_output(
        master_nb_path,
        FILE_MANAGER.get_path("jupyterlite-correct"),
        assert_dirs_equal_kwargs=dict(variable_path_exts=[".zip"]),
    )
