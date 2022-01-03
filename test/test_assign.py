##################################
##### Tests for otter assign #####
##################################

import os
import pytest
import shutil
import subprocess

from glob import glob
from unittest.mock import patch

from otter.assign import main as assign
from otter.assign.tests import determine_question_point_value, Test
from otter.generate.token import APIClient

from .utils import assert_dirs_equal, TestFileManager


FILE_MANAGER = TestFileManager("test/test-assign")


@pytest.fixture
def cleanup_assign_output(cleanup_enabled):
    """
    Removes assign output
    """
    yield
    if cleanup_enabled and os.path.exists(FILE_MANAGER.get_path("output")):
            shutil.rmtree(FILE_MANAGER.get_path("output"))


def check_gradescope_zipfile(path, correct_dir_path):
    ag_path = FILE_MANAGER.get_path("autograder")

    # unzip the zipfile
    unzip_command = ["unzip", "-o", path, "-d", ag_path]
    unzip = subprocess.run(unzip_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert len(unzip.stderr) == 0, unzip.stderr.decode("utf-8")

    assert_dirs_equal(ag_path, correct_dir_path)

    # cleanup
    if os.path.exists(ag_path):
        shutil.rmtree(ag_path)


def assign_and_check_output(nb_path, correct_dir, assign_kwargs={}, assert_dirs_equal_kwargs={}):
    """
    """
    output_path = FILE_MANAGER.get_path("output")
    assign(nb_path, output_path, **assign_kwargs)
    assert_dirs_equal(output_path, correct_dir, **assert_dirs_equal_kwargs)


def test_convert_example(cleanup_assign_output):
    """
    Checks that otter assign filters and outputs correctly
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("example.ipynb"), 
        FILE_MANAGER.get_path("example-correct"), 
        assign_kwargs=dict(
            no_run_tests=True, 
            v1=True,
        ),
    )

    
def test_otter_example(cleanup_assign_output):
    """
    Checks that otter assign filters and outputs correctly, as well as creates a correct .otter file
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("generate-otter.ipynb"), 
        FILE_MANAGER.get_path("otter-correct"), 
    )


def test_pdf_example(cleanup_assign_output):
    """
    Checks that otter assign filters and outputs correctly, as well as creates a correct .zip file along with PDFs
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("generate-pdf.ipynb"),
        FILE_MANAGER.get_path("pdf-correct"),
        assign_kwargs=dict(no_run_tests=True),
        assert_dirs_equal_kwargs=dict(ignore_ext=[".pdf"], variable_path_exts=[".zip"]),
    )


@patch.object(APIClient, "get_token")
def test_gradescope_example(mocked_client, cleanup_assign_output):
    """
    Checks that otter assign filters and outputs correctly, as well as creates a correct .zip file along with PDFs.
    Additionally, includes testing Gradescope integration.
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


def test_r_example(cleanup_assign_output):
    """
    Checks that otter assign works for R notebooks correctly
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("r-example.ipynb"),
        FILE_MANAGER.get_path("r-correct"),
        assign_kwargs=dict(v1=True),
        assert_dirs_equal_kwargs=dict(ignore_ext=[".pdf"], variable_path_exts=[".zip"]),
    )


def test_rmd_example(cleanup_assign_output):
    """
    Checks that otter assign works for Rmd files
    """
    assign_and_check_output(
        FILE_MANAGER.get_path("rmd-example.Rmd"),
        FILE_MANAGER.get_path("rmd-correct"),
        assign_kwargs=dict(v1=True),
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


def test_point_value_rounding(cleanup_assign_output):
    """
    Tests that point values are rounded appropriately.
    """
    # sum(4 / 11 for _ in range(11)) evaluates to 4.000000000000001 in Python, so this will
    # check that the per-test-case point values are correctly rounded.
    points = determine_question_point_value({
        "points": None,
        "manual": False,
    }, [Test("", "", False, 4 / 11, "", "") for _ in range(11)])
    assert points == 4
