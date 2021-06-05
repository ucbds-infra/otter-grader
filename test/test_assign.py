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

# from otter.argparser import get_parser
from otter.assign import main as assign
from otter.generate.token import APIClient
from otter.runner import run_otter

from . import TestCase

TEST_FILES_PATH = "test/test-assign/"

class TestAssign(TestCase):

    def check_gradescope_zipfile(self, path, correct_dir_path):
        # unzip the zipfile
        unzip_command = ["unzip", "-o", path, "-d", TEST_FILES_PATH + "autograder"]
        unzip = subprocess.run(unzip_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(unzip.stderr), 0, unzip.stderr.decode("utf-8"))

        self.assertDirsEqual(TEST_FILES_PATH + "autograder", correct_dir_path, ignore_ext=[])

        # cleanup
        if os.path.exists(TEST_FILES_PATH + "autograder"):
            shutil.rmtree(TEST_FILES_PATH + "autograder")

    def test_convert_example(self):
        """
        Checks that otter assign filters and outputs correctly
        """
        # run otter assign
        run_assign_args = [
            "assign", "--no-run-tests", TEST_FILES_PATH + "example.ipynb", TEST_FILES_PATH + "output",
        ]
        # args = parser.parse_args(run_assign_args)
        # args.func = assign
        # args.func(args)
        run_otter(run_assign_args)
       
        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "example-correct")
        
    def test_otter_example(self):
        """
        Checks that otter assign filters and outputs correctly, as well as creates a correct .otter file
        """
        run_assign_args = [
            "assign",  TEST_FILES_PATH + "generate-otter.ipynb", 
            TEST_FILES_PATH + "output",
        ]
        # args = parser.parse_args(run_assign_args)
        # args.func = assign
        # args.func(args)
        run_otter(run_assign_args)
        
        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "otter-correct")     

    def test_pdf_example(self):
        """
        Checks that otter assign filters and outputs correctly, as well as creates a correct .zip file along with PDFs
        """
        run_assign_args = [
            "assign", "--no-run-tests", TEST_FILES_PATH + "generate-pdf.ipynb", TEST_FILES_PATH + "output",
        ]
        # args = parser.parse_args(run_assign_args)
        # args.func = assign
        # args.func(args)
        run_otter(run_assign_args)
      
        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "pdf-correct", ignore_ext=[".pdf",".zip"])
        
        # # check gradescope zip file
        # self.check_gradescope_zipfile(
        #     TEST_FILES_PATH + "output/autograder/autograder.zip", TEST_FILES_PATH + "pdf-autograder-correct",
        # )
    
    @patch.object(APIClient,"get_token")
    def test_gradescope_example(self, mocked_client):

        """
        Checks that otter assign filters and outputs correctly, as well as creates a correct .zip file along with PDFs.
        Additionally, includes testing Gradescope integration.
        """

        mocked_client.return_value = 'token'
        
        run_gradescope_args = [
            "assign", "--no-run-tests", TEST_FILES_PATH + "generate-gradescope.ipynb", 
            TEST_FILES_PATH + "output",
        ]
        # args = parser.parse_args(run_gradescope_args)
        # args.func = assign
        # args.func(args)
        run_otter(run_gradescope_args)
      
        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "gs-correct", ignore_ext=[".pdf",".zip"])

        # check gradescope zip file
        self.check_gradescope_zipfile(
            TEST_FILES_PATH + "output/autograder/autograder.zip", TEST_FILES_PATH + "gs-autograder-correct",
        )

    def test_r_example(self):
        """
        Checks that otter assign works for R notebooks correctly
        """
        run_assign_args = [
            "assign", TEST_FILES_PATH + "r-example.ipynb", 
            TEST_FILES_PATH + "output",
        ]
        # args = parser.parse_args(run_assign_args)
        # args.func = assign
        # args.func(args)
        run_otter(run_assign_args)

        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "r-correct", ignore_ext=[".pdf",".zip"])
        
        # # check gradescope zip file
        # self.check_gradescope_zipfile(
        #     TEST_FILES_PATH + "output/autograder/autograder.zip", TEST_FILES_PATH + "r-autograder-correct",
        # )

    def test_rmd_example(self):
        """
        Checks that otter assign works for Rmd files
        """
        run_assign_args = [
            "assign", TEST_FILES_PATH + "rmd-example.Rmd", 
            TEST_FILES_PATH + "output",
        ]
        # args = parser.parse_args(run_assign_args)
        # args.func = assign
        # args.func(args)
        run_otter(run_assign_args)

        self.assertDirsEqual(TEST_FILES_PATH + "output", TEST_FILES_PATH + "rmd-correct", ignore_ext=[".zip"])
        
        # check gradescope zip file
        self.check_gradescope_zipfile(
            TEST_FILES_PATH + "output/autograder/autograder.zip", TEST_FILES_PATH + "rmd-autograder-correct",
        )

    def tearDown(self):
        """
        Removes assign output
        """
        # cleanup
        if os.path.exists(TEST_FILES_PATH + "output"):
            shutil.rmtree(TEST_FILES_PATH + "output")
