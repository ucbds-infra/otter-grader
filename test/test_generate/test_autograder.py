"""Tests for ``otter.generate``"""

import os
import pytest

from unittest import mock

from otter.generate import main as generate

from ..utils import assert_dirs_equal, TestFileManager, unzip_to_temp


FILE_MANAGER = TestFileManager("test/test_generate/test-autograder")
OUTPUT_PATH = FILE_MANAGER.get_path("autograder.zip")


@pytest.fixture(autouse=True)
def cleanup_output(cleanup_enabled):
    yield
    if cleanup_enabled and os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)


def test_autograder():
    """
    Check that the correct zip file is generated.
    """
    # create the zipfile
    generate(
        tests_dir = FILE_MANAGER.get_path("tests"),
        output_path = OUTPUT_PATH,
        requirements = FILE_MANAGER.get_path("requirements.txt"),
        files = [FILE_MANAGER.get_path("data/test-df.csv")],
        no_environment = True,  # don't use the environment.yml in the root of the repo
    )

    with unzip_to_temp(FILE_MANAGER.get_path("autograder.zip")) as unzipped_dir:
        assert_dirs_equal(unzipped_dir, FILE_MANAGER.get_path("autograder-correct"))


def test_autograder_with_token():
    """
    Check that the correct zip file is generated when a token is specified instead of a username
    and password.

    This test also checks that directories are copied correctly when listed in the ``files``
    argument.
    """
    # create the zipfile
    with mock.patch("otter.generate.APIClient") as mocked_client:
        generate(
            tests_dir = FILE_MANAGER.get_path("tests"),
            output_path = OUTPUT_PATH,
            requirements = FILE_MANAGER.get_path("requirements.txt"),
            config = FILE_MANAGER.get_path("otter_config.json"),
            files = [FILE_MANAGER.get_path("data")],
            no_environment = True,  # don't use the environment.yml in the root of the repo
        )
        mocked_client.assert_not_called()

    with unzip_to_temp(FILE_MANAGER.get_path("autograder.zip")) as unzipped_dir:
        assert_dirs_equal(unzipped_dir, FILE_MANAGER.get_path("autograder-token-correct"))


def test_custom_env():
    """
    Check that a custom environment.yml is correctly read and modified.
    """
    # create the zipfile
    generate(
        tests_dir = FILE_MANAGER.get_path("tests"),
        output_path = OUTPUT_PATH,
        requirements = FILE_MANAGER.get_path("requirements.txt"),
        environment = FILE_MANAGER.get_path("environment.yml"),
        files = [FILE_MANAGER.get_path("data/test-df.csv")],
    )

    with unzip_to_temp(FILE_MANAGER.get_path("autograder.zip")) as unzipped_dir:
        assert_dirs_equal(unzipped_dir, FILE_MANAGER.get_path("autograder-custom-env"))


def test_lang_r():
    """
    Check that the R autograder configuration is generated correctly.
    """
    # create the zipfile
    generate(
        tests_dir = FILE_MANAGER.get_path("tests"),
        output_path = OUTPUT_PATH,
        config = FILE_MANAGER.get_path("r_otter_config.json"),
        no_environment = True,
    )

    with unzip_to_temp(FILE_MANAGER.get_path("autograder.zip")) as unzipped_dir:
        assert_dirs_equal(unzipped_dir, FILE_MANAGER.get_path("autograder-r-correct"))
