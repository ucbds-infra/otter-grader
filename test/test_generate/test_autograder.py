####################################
##### Tests for otter generate #####
####################################

import json
import os
import shutil
import subprocess
import unittest

from glob import glob
from subprocess import PIPE
from unittest import mock

from otter.generate import main as generate

from .. import TestCase


TEST_FILES_PATH = "test/test_generate/test-autograder/"


class TestAutograder(TestCase):

    def test_autograder(self):
        """
        Check that the correct zipfile is created by gs_generator.py
        """
        # create the zipfile
        generate(
            tests_path = TEST_FILES_PATH + "tests",
            output_dir = TEST_FILES_PATH,
            requirements = TEST_FILES_PATH + "requirements.txt",
            files = [TEST_FILES_PATH + "data/test-df.csv"],
            no_environment = True,  # don't use the environment.yml in the root of the repo
        )

        with self.unzip_to_temp(TEST_FILES_PATH + "autograder.zip", delete=True) as unzipped_dir:
            self.assertDirsEqual(unzipped_dir, TEST_FILES_PATH + "autograder-correct")

    def test_autograder_with_token(self):
        """
        Checks otter assign with token specified instead of username and password.
        """
        # create the zipfile
        with mock.patch("otter.generate.APIClient") as mocked_client:
            generate(
                tests_path = TEST_FILES_PATH + "tests",
                output_dir = TEST_FILES_PATH,
                requirements = TEST_FILES_PATH + "requirements.txt",
                config = TEST_FILES_PATH + "otter_config.json",
                files = [TEST_FILES_PATH + "data/test-df.csv"],
                no_environment = True,  # don't use the environment.yml in the root of the repo
            )
            mocked_client.assert_not_called()
    
        with self.unzip_to_temp(TEST_FILES_PATH + "autograder.zip", delete=True) as unzipped_dir:
            self.assertDirsEqual(unzipped_dir, TEST_FILES_PATH + "autograder-token-correct")

    def test_custom_env(self):
        """
        Check that a custom environment.yml is correctly read and modified
        """
        # create the zipfile
        generate(
            tests_path = TEST_FILES_PATH + "tests",
            output_dir = TEST_FILES_PATH,
            requirements = TEST_FILES_PATH + "requirements.txt",
            environment = TEST_FILES_PATH + "environment.yml",
            files = [TEST_FILES_PATH + "data/test-df.csv"],
        )

        with self.unzip_to_temp(TEST_FILES_PATH + "autograder.zip", delete=True) as unzipped_dir:
            self.assertDirsEqual(unzipped_dir, TEST_FILES_PATH + "autograder-custom-env")
