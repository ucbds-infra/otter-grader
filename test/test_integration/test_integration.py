"""Integration test for Otter-Grader's pipeline"""

import os
import pytest
import shutil

from click.testing import CliRunner
from glob import glob

from otter.cli import cli

from ..utils import assert_dirs_equal, TestFileManager, unzip_to_temp


FILE_MANAGER = TestFileManager(__file__, True)
OUTPUT_DIR = FILE_MANAGER.get_path("output")
RUNNER = CliRunner()

get_output_dir = lambda subdir: os.path.join(OUTPUT_DIR, subdir)

# TODO: disable pdf generation; see disable_pdf_generation in assign tests


@pytest.fixture(autouse=True)
def cleanup(cleanup_enabled):
    """"""
    yield
    if cleanup_enabled and os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)


def do_assign_test(output_dir):
    """
    Run Otter Assign, verify its output, and return the path to the autograder zip file.
    """
    RUNNER.invoke(cli, ["assign", FILE_MANAGER.get_path("proj03.ipynb"), output_dir])

    assert_dirs_equal(
        output_dir,
        FILE_MANAGER.get_path("expected-dist"),
        ignore_ext=[".pdf"],
        variable_path_exts=[".zip"],
        ignore_log=True,
    )

    ag_zip_path = glob(os.path.join(output_dir, "autograder", "*.zip"))[0]
    with unzip_to_temp(ag_zip_path) as unzipped_ag_path:
        assert_dirs_equal(unzipped_ag_path, FILE_MANAGER.get_path("expected-autograder-zip"))

    return ag_zip_path


def do_grade_test(ag_zip_path, output_dir):
    """"""
    RUNNER.invoke(cli, [
        "grade",
        "-p", FILE_MANAGER.get_path("submissions"),
        "-a", ag_zip_path,
        "-o", output_dir,
    ])


@pytest.mark.slow
def test_integration():
    """"""
    ag_zip_path = do_assign_test(get_output_dir("assign"))

    do_grade_test(ag_zip_path,get_output_dir("grade"))
