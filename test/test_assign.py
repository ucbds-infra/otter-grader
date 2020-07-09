##################################
##### Tests for otter assign #####
##################################

import unittest
import sys
import os
import shutil
import subprocess

from subprocess import PIPE
from glob import glob
from unittest.mock import patch

from otter.argparser import get_parser
from otter.assign import main as assign
from otter.generate.token import APIClient


parser = get_parser()

TEST_FILES_PATH = "test/test-assign/"

class TestAssign(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n\n\n" + ("=" * 60) + f"\nRunning {__name__}.{cls.__name__}\n" + ("=" * 60) + "\n")

    def check_gradescope_zipfile(self, path, correct_dir_path, config, tests=[], files=[]):
        # unzip the zipfile
        unzip_command = ["unzip", "-o", path, "-d", TEST_FILES_PATH + "autograder"]
        unzip = subprocess.run(unzip_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(unzip.stderr), 0, unzip.stderr.decode("utf-8"))

        self.assertDirsEqual(TEST_FILES_PATH + "autograder", correct_dir_path, ignore_ext=[])

        # cleanup
        if os.path.exists(TEST_FILES_PATH + "autograder"):
            shutil.rmtree(TEST_FILES_PATH + "autograder")

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
        args.func = assign
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
        args.func = assign
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
        args.func = assign
        args.func(args)

        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "pdf-correct", ignore_ext=[".pdf",".zip"])
        
        # check gradescope zip file
        self.check_gradescope_zipfile(
            TEST_FILES_PATH + "output/autograder/autograder.zip", TEST_FILES_PATH + "pdf-autograder-correct",
            {
                "seed": 42,
                "show_stdout_on_release": True,
                "show_hidden_tests_on_release": True,
            },  ["q1.py","q3.py","q8.py"], ["data.csv"]
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
        args.func = assign
        args.func(args)
        
        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "gs-correct", ignore_ext=[".pdf",".zip"])

        # check gradescope zip file
        
        self.check_gradescope_zipfile(
            TEST_FILES_PATH + "output/autograder/autograder.zip", TEST_FILES_PATH + "gs-autograder-correct",
            {
                "seed": 42,
                "show_stdout_on_release": True,
                "show_hidden_tests_on_release": True,
                "token": 'token',
                "course_id": '123',
                "assignment_id": '567',
                "filtering": True
            },  ["q1.py","q3.py","q8.py"], ["data.csv"]
        )
        # cleanup
        if os.path.exists(TEST_FILES_PATH + "output"):
            shutil.rmtree(TEST_FILES_PATH + "output")
        
