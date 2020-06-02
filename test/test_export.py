#################################
##### Tests for otter export #####
#################################

import os
import unittest
import subprocess
import json
import re
import contextlib
import nbconvert

from io import StringIO
from unittest import mock
from subprocess import Popen, PIPE
from glob import glob

from otter.export import export_notebook

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test-export/"

class TestExport(unittest.TestCase):

    # TODO: stable method of pdf content checking

    def test_success_HTML(self):
        test_file = "successful-html-test"
        grade_command = ["export", "--filtering", 
            TEST_FILES_PATH + test_file + ".ipynb"
        ]
        args = parser.parse_args(grade_command)
        args.func(args)
        #check existence of pdf
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file+".pdf"))

        #TODO: checks for equality

        #cleanup
        cleanup_command = ["rm", TEST_FILES_PATH + test_file + ".pdf"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup: " + str(cleanup.stderr))
        pass
        
    def test_success_pagebreak(self):
        """
        tests a successful filter with pagebreaks
        """
        test_file = "success-pagebreak-test"
        grade_command = ["export", "--filtering",
            "--pagebreaks", 
            TEST_FILES_PATH + test_file + ".ipynb"
        ]
        args = parser.parse_args(grade_command)
        args.func(args)
        #check existence of pdf
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file+".pdf"))

        # TODO : checks for equality 

        #cleanup
        cleanup_command = ["rm", TEST_FILES_PATH + test_file + ".pdf"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup: " + str(cleanup.stderr))
        pass

    def test_no_open(self):
        """
        tests a filter without an open 
        """
        test_file = "no-open-tag-test"
        grade_command = ["export", "--filtering",
            TEST_FILES_PATH + test_file + ".ipynb"
        ]
        try:
            args = parser.parse_args(grade_command)
            args.func(args)
        except nbconvert.pdf.LatexFailed as error:
            print("No opening comment detected")
            pass

    def test_no_close(self):
        """
        tests a filter without a close
        """
        test_file = "no-close-tag-test"
        grade_command = ["export", "--filtering",
            "--pagebreaks", 
            TEST_FILES_PATH + test_file + ".ipynb"
        ]
        args = parser.parse_args(grade_command)
        args.func(args)
        #check existence of pdf
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file+".pdf"))

        # TODO : checks for equality 

        #cleanup
        cleanup_command = ["rm", TEST_FILES_PATH + test_file + ".pdf"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup:" + str(cleanup.stderr))
        pass