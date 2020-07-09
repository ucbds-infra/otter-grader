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
import nbformat

from io import StringIO
from unittest import mock
from subprocess import Popen, PIPE
from glob import glob
from textwrap import dedent

from otter.export import export_notebook
from otter.export import main as export
from otter.export.filter import load_notebook

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test-export/"

class TestExport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n\n\n" + ("=" * 60) + f"\nRunning {__name__}.{cls.__name__}\n" + ("=" * 60) + "\n")

    def test_success_HTML(self):
        """
        Tests a successful export with filtering and no pagebreaks
        """
        test_file = "successful-html-test"
        grade_command = ["export", "--filtering", "-s",
            TEST_FILES_PATH + test_file + ".ipynb"
        ]
        args = parser.parse_args(grade_command)
        args.func = export
        args.func(args)

        # check existence of pdf and tex
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file + ".pdf"))
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file + ".tex"))

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
        args.func = export
        args.func(args)

        # check existence of pdf and tex
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file + ".pdf"))
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file + ".tex"))

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

        should_contain = [
            "There was an error generating your LaTeX\nShowing concise error message\n" + "=" * 60,
            "(There were 3 error messages)",
            "This is BibTeX"
        ]

        args = parser.parse_args(grade_command)
        args.func = export

        actual_output = StringIO()
        with contextlib.redirect_stdout(actual_output):
            args.func(args)

        for s in should_contain:
            self.assertIn(s, actual_output.getvalue(), 
                f"Empty Tex did not contain substring: {s}\n\n"
                "Output:\n\n{actual_output.getvalue()}")

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
        args.func = export
        args.func(args)

        # check existence of pdf and tex
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file + ".pdf"))
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file + ".tex"))

        # cleanup

        cleanup_command = ["rm", TEST_FILES_PATH + test_file + ".pdf", TEST_FILES_PATH + test_file + ".tex"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup:" + str(cleanup.stderr))

    def test_load_notebook(self):
        """
        Tests a successful load_notebook
        """
        test_file = "successful-html-test"
        node = load_notebook(TEST_FILES_PATH + test_file + ".ipynb")

        nbformat.write(node, TEST_FILES_PATH + test_file)

        # check existence of file
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file))
        self.assertTrue(filecmp.cmp(TEST_FILES_PATH + test_file, TEST_FILES_PATH + "correct/" + test_file))
        
        # cleanup
        cleanup_command = ["rm", TEST_FILES_PATH + test_file]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup: " + str(cleanup.stderr))
