##################################
##### Tests for otter assign #####
##################################

import unittest
import sys
import os
import shutil
import subprocess
import contextlib

from io import StringIO
from subprocess import PIPE
from glob import glob
from unittest.mock import patch

from otter.argparser import get_parser
from otter.utils import block_print
from otter.generate.token import APIClient


parser = get_parser()

TEST_FILES_PATH = "test/test-assign/"

class TestAssign(unittest.TestCase):

    def check_gradescope_zipfile(self, path, correctPath, config, tests=[], files=[]):
        # unzip the zipfile
        unzip_command = ["unzip", "-o", path, "-d", TEST_FILES_PATH + "autograder"]
        unzip = subprocess.run(unzip_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(unzip.stderr), 0, unzip.stderr)

        expected_files = ["run_autograder", "setup.sh", "requirements.txt"]
        expected_directories = ["tests", "files"]

        # go through files and ensure that they all exist
        for file in expected_files:
            fp = TEST_FILES_PATH + "autograder/" + file
            self.assertTrue(os.path.isfile(fp), f"File {fp} does not exist")
        
        for drct in expected_directories:
            dp = TEST_FILES_PATH + "autograder/" + drct
            self.assertTrue(os.path.isdir(dp), f"Directory {dp} does not exist")
        
        for file in files:
            fp = TEST_FILES_PATH + "autograder/files/" + file
            self.assertTrue(os.path.isfile(fp), f"Support file {fp} does not exist")
        
        for test in tests:
            tp = TEST_FILES_PATH + "autograder/tests/" + test
            self.assertTrue(os.path.isfile(tp), f"Test file {tp} does not exist")

        # check configurations in autograder/run_autograder
        with open(TEST_FILES_PATH + "autograder/run_autograder") as f:
            run_autograder = f.read()

        # exec with __name__ not __main__ so that the grading doesn't occur and it only loads globals
        run_autograder_globals = {"__name__": "__not_main__"}
        exec(run_autograder, run_autograder_globals)

        for k, v in config.items():
            self.assertEqual(run_autograder_globals["config"][k], v, 
                f"Expected config value for {k} ({v}) does not match actual value ({run_autograder_globals[k]})"
            )
        
        # assumed correct dir checking

        unzip_command = ["unzip", "-o", correctPath, "-d", TEST_FILES_PATH + "autograder-correct"]
        unzip = subprocess.run(unzip_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(unzip.stderr), 0, unzip.stderr)

        self.assertDirsEqual(TEST_FILES_PATH + "autograder",TEST_FILES_PATH + "autograder-correct", ignore_ext=[])

        # cleanup
        if os.path.exists(TEST_FILES_PATH + "autograder"):
            shutil.rmtree(TEST_FILES_PATH + "autograder")
        if os.path.exists(TEST_FILES_PATH + "autograder-correct"):
            shutil.rmtree(TEST_FILES_PATH + "autograder-correct")

    def assertFilesEqual(self, p1, p2):
        try:
            with open(p1) as f1:
                with open(p2) as f2:
                    self.assertEqual(f1.read(), f2.read(), f"Contents of {p1} did not equal contents of {p2}")
        
        except UnicodeDecodeError:
            with open(p1, "rb") as f1:
                with open(p2, "rb") as f2:
                    self.assertEqual(f1.read(), f2.read(), f"Contents of {p1} did not equal contents of {p2}")

    def assertDirsEqual(self, dir1, dir2, ignore_ext=[]):
        self.assertTrue(os.path.exists(dir1), f"{dir1} does not exist")
        self.assertTrue(os.path.exists(dir2), f"{dir2} does not exist")
        self.assertTrue(os.path.isfile(dir1) == os.path.isfile(dir2), f"{dir1} and {dir2} have different type")

        if os.path.isfile(dir1):
            if os.path.splitext(dir1)[1] not in ignore_ext:
                self.assertFilesEqual(dir1, dir2)

        else:
            self.assertEqual(os.listdir(dir1), os.listdir(dir2), f"{dir1} and {dir2} have different contents")
            for f1, f2 in zip(os.listdir(dir1), os.listdir(dir2)):
                f1, f2 = os.path.join(dir1, f1), os.path.join(dir2, f2)
                self.assertDirsEqual(f1, f2, ignore_ext=ignore_ext)
    
    def test_convert_example(self):
        """
        Checks that otter assign filters and outputs correctly
        """
        # run otter assign
        run_assign_args = [
            "assign", "--no-run-tests", TEST_FILES_PATH + "example.ipynb", TEST_FILES_PATH + "output", "data.csv"
        ]
        args = parser.parse_args(run_assign_args)

        # block stdout while running
        output = StringIO()
        with block_print():
            args.func(args)

        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "example-correct")

        # cleanup
        if os.path.exists(TEST_FILES_PATH + "output"):
            shutil.rmtree(TEST_FILES_PATH + "output")

    def test_otter_example(self):
        """
        Checks that otter assign filters and outputs correctly, as well as creates a correct .otter file
        """
        run_assign_args = [
            "assign", "--no-init-cell", "--no-check-all", TEST_FILES_PATH + "generate-otter.ipynb", 
            TEST_FILES_PATH + "output", "data.csv"
        ]
        args = parser.parse_args(run_assign_args)

        # block stdout while running
        output = StringIO()
        with contextlib.redirect_stdout(output):
            with patch("otter.assign.block_print"):
                args.func(args)

        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "otter-correct")

        # cleanup
        if os.path.exists(TEST_FILES_PATH + "output"):
            shutil.rmtree(TEST_FILES_PATH + "output")      

    def test_pdf_example(self):
        """
        Checks that otter assign filters and outputs correctly, as well as creates a correct .zip file along with PDFs
        """
        run_assign_args = [
            "assign", "--no-run-tests", TEST_FILES_PATH + "generate-pdf.ipynb", TEST_FILES_PATH + "output", "data.csv"
        ]
        args = parser.parse_args(run_assign_args)

        # block stdout while running

        output = StringIO()
        with block_print():
            args.func(args)

        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "pdf-correct", ignore_ext=[".pdf",".zip"])
        
        # check gradescope zip file
        self.check_gradescope_zipfile(
            TEST_FILES_PATH + "output/autograder/autograder.zip", TEST_FILES_PATH + "pdf-correct/autograder/autograder.zip",
            {},  ["q1.py","q3.py","q8.py"], ["data.csv"]
        )

        # cleanup
        if os.path.exists(TEST_FILES_PATH + "output"):
            shutil.rmtree(TEST_FILES_PATH + "output")
    
    @patch.object(APIClient,"get_token")
    def test_gradescope_example(self, mocked_client):

        """
        Checks that otter assign filters and outputs correctly, as well as creates a correct .zip file along with PDFs.
        Additionally, includes testing Gradescope integration.
        """

        mocked_client.return_value = 'token'
        
        run_gradescope_args = [
            "assign", "--no-run-tests", "--no-check-all", TEST_FILES_PATH + "generate-gradescope.ipynb", 
            TEST_FILES_PATH + "output", "data.csv"
        ]
        args = parser.parse_args(run_gradescope_args)

        output = StringIO()
        with block_print():
            args.func(args)
        
        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "gs-correct", ignore_ext=[".pdf",".zip"])

        # check gradescope zip file
        self.check_gradescope_zipfile(
            TEST_FILES_PATH + "output/autograder/autograder.zip", TEST_FILES_PATH + "gs-correct/autograder/autograder.zip",
            {},  ["q1.py","q3.py","q8.py"], ["data.csv"]
        )

        # cleanup
        if os.path.exists(TEST_FILES_PATH + "output"):
            shutil.rmtree(TEST_FILES_PATH + "output")
        
