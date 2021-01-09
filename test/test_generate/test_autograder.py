####################################
##### Tests for otter generate #####
####################################

import os
import unittest
import subprocess
import json

from subprocess import PIPE
from glob import glob
from unittest import mock

# from otter.argparser import get_parser
from otter.generate.autograder import main as autograder
from otter.runner import run_otter

from .. import TestCase

# parser = get_parser()

TEST_FILES_PATH = "test/test_generate/test-autograder/"

class TestAutograder(TestCase):

    def test_autograder(self):
        """
        Check that the correct zipfile is created by gs_generator.py
        """
        # create the zipfile
        generate_command = [
            "generate",
            "-t", TEST_FILES_PATH + "tests",
            "-o", TEST_FILES_PATH,
            "-r", TEST_FILES_PATH + "requirements.txt",
            TEST_FILES_PATH + "data/test-df.csv"
        ]
        # args = parser.parse_args(generate_command)
        # args.func = autograder
        # args.func(args)
        run_otter(generate_command)

        with self.unzip_to_temp(TEST_FILES_PATH + "autograder.zip", delete=True) as unzipped_dir:
            self.assertDirsEqual(unzipped_dir, TEST_FILES_PATH + "autograder-correct")
