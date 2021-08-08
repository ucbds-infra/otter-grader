##################################
##### Tests for Otter Export #####
##################################

# NOTES:
# - tests do not check for PDF equality

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
from otter.export.exporters.base_exporter import BaseExporter

from . import TestCase


TEST_FILES_PATH = "test/test-export/"


class TestExport(TestCase):

    @staticmethod
    def run_export(notebook_stem, **kwargs):
        export(TEST_FILES_PATH + notebook_stem + ".ipynb", **kwargs)

    def test_success_HTML(self):
        """
        Tests a successful export with filtering and no pagebreaks
        """
        test_file = "successful-html-test"
        self.run_export(test_file, filtering=True, save=True, exporter="latex")

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
        self.run_export(test_file, filtering=True, exporter="latex", pagebreaks=True, save=True)

        # check existence of pdf and tex
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file + ".pdf"))
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file + ".tex"))

        # cleanup
        cleanup_command = ["rm", TEST_FILES_PATH + test_file + ".pdf", TEST_FILES_PATH + test_file + ".tex"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup: " + str(cleanup.stderr))

    def test_no_close(self):
        """
        Tests a filtered export without a closing comment
        """
        test_file = "no-close-tag-test"
        self.run_export(test_file, filtering=True, exporter="latex", pagebreaks=True, save=True)

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
        node = BaseExporter.load_notebook(TEST_FILES_PATH + test_file + ".ipynb", filtering=True)

        nbformat.write(node, TEST_FILES_PATH + test_file)

        # check existence of file
        self.assertTrue(os.path.isfile(TEST_FILES_PATH + test_file))
        self.assertTrue(filecmp.cmp(TEST_FILES_PATH + test_file, TEST_FILES_PATH + "correct/" + test_file))
        
        # cleanup
        cleanup_command = ["rm", TEST_FILES_PATH + test_file]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup: " + str(cleanup.stderr))
