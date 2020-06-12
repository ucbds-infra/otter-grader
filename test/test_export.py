##################################
##### Tests for Otter Export #####
##################################

# NOTES:
# - tests do not check for PDF equality but rather have exporter save the TeX file as well
#   and check that the TeX is correct (assuming that TeX conversion works correctly) and checks
#   that PDF file exists

import os
import unittest
import subprocess
import json
import re
import contextlib
import nbconvert
import filecmp

from io import StringIO
from unittest import mock
from subprocess import Popen, PIPE
from glob import glob
from textwrap import dedent

from otter.export import export_notebook

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test-export/"

class TestExport(unittest.TestCase):

    def test_success_HTML(self):
        """
        Tests a successful export with filtering and no pagebreaks
        """
        test_file = "successful-html-test"
        grade_command = ["export", "--filtering", "-s",
            TEST_FILES_PATH + test_file + ".ipynb"
        ]
        args = parser.parse_args(grade_command)
        args.func(args)

        # check existence of pdf
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file+".pdf"))

        # check correct TeX
        with open(TEST_FILES_PATH + test_file + ".tex") as actual:
            with open(TEST_FILES_PATH + "/correct/" + test_file + ".tex") as expected:
                actual_contents = actual.read()
                expected_contents = expected.read()
                self.assertEqual(actual_contents, expected_contents, f"TeX is not equal: \n\n{actual_contents}")

        # cleanup
        cleanup_command = ["rm", TEST_FILES_PATH + test_file + ".pdf", TEST_FILES_PATH + test_file + ".tex"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup: " + str(cleanup.stderr))
        
    def test_success_pagebreak(self):
        """
        Tests a successful filter with pagebreaks
        """
        test_file = "success-pagebreak-test"
        grade_command = ["export", "--filtering",
            "--pagebreaks", "-s",
            TEST_FILES_PATH + test_file + ".ipynb"
        ]
        args = parser.parse_args(grade_command)
        args.func(args)

        # check existence of pdf
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file+".pdf"))

        # check correct TeX
        with open(TEST_FILES_PATH + test_file + ".tex") as actual:
            with open(TEST_FILES_PATH + "/correct/" + test_file + ".tex") as expected:
                actual_contents = actual.read()
                expected_contents = expected.read()
                self.assertEqual(actual_contents, expected_contents, f"TeX is not equal: \n\n{actual_contents}")

        # cleanup
        cleanup_command = ["rm", TEST_FILES_PATH + test_file + ".pdf", TEST_FILES_PATH + test_file + ".tex"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup: " + str(cleanup.stderr))

    def test_no_open(self):
        """
        Tests a filtered export without an opening comment
        """
        test_file = "no-open-tag-test"
        grade_command = ["export", "--filtering",
            TEST_FILES_PATH + test_file + ".ipynb"
        ]

        expected_output = dedent("""\
        There was an error generating your LaTeX
        Showing concise error message
        ============================================================
        This is BibTeX, Version 0.99d (TeX Live 2020)
        The top-level auxiliary file: ./notebook.aux
        I found no \\citation commands---while reading file ./notebook.aux
        I found no \\bibdata command---while reading file ./notebook.aux
        I found no \\bibstyle command---while reading file ./notebook.aux
        (There were 3 error messages)

        ============================================================
        """)

        args = parser.parse_args(grade_command)

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            args.func(args)

        self.assertAlmostEqual(
            actual_output.getvalue().strip(), 
            expected_output.strip(), 
            f"Empty TeX did not fail: \n\n{actual_output.getvalue()}"
        )

    def test_no_close(self):
        """
        Tests a filtered export without a closing comment
        """
        test_file = "no-close-tag-test"
        grade_command = ["export", "--filtering",
            "--pagebreaks", "-s",
            TEST_FILES_PATH + test_file + ".ipynb"
        ]
        args = parser.parse_args(grade_command)
        args.func(args)

        # check existence of pdf
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file+".pdf"))

        # check correct TeX
        with open(TEST_FILES_PATH + test_file + ".tex") as actual:
            with open(TEST_FILES_PATH + "/correct/" + test_file + ".tex") as expected:
                actual_contents = actual.read()
                expected_contents = expected.read()
                self.assertEqual(actual_contents, expected_contents, f"TeX is not equal: \n\n{actual_contents}")

        # cleanup
        cleanup_command = ["rm", TEST_FILES_PATH + test_file + ".pdf", TEST_FILES_PATH + test_file + ".tex"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup:" + str(cleanup.stderr))
