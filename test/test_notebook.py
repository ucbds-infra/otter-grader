##################################
##### Tests for otter notebook #####
##################################

import unittest
import sys
import os
import shutil
import subprocess

from subprocess import PIPE
from glob import glob
from unittest.mock import patch

from otter import Notebook
from otter.check.logs import LogEntry, EventType, Log
from otter.check.notebook import _OTTER_LOG_FILENAME

from . import TestCase

TEST_FILES_PATH = "test/test-notebook/"

# functions used in one of the tests below
def square(x):
    return x**2

def negate(x):
    return not x

class TestNotebook(TestCase):
    """
    Test cases for the ``Notebook`` class
    """

    def test_check(self):
        """
        Checks that the otter.Notebook class works correctly
        """
        grader = Notebook(TEST_FILES_PATH + "tests")

        def square(x):
            return x**2

        def negate(x):
            return not x

        global_env = {
            "square" : square,
            "negate" : negate
        }

        for q_path in glob(TEST_FILES_PATH + "tests/*.py"):
            q = os.path.split(q_path)[1][:-3]
            result = grader.check(q, global_env=global_env)
            if q != "q2":
                self.assertEqual(result.grade, 1, "Test {} failed".format(q))
            else:
                self.assertEqual(result.grade, 0, "Test {} passed".format(q))

    def test_check_no_env(self):
        """
        Checks that the ``Notebook`` class works correctly, with no global env input
        """
        grader = Notebook(TEST_FILES_PATH + "tests")

        for q_path in glob(TEST_FILES_PATH + "tests/*.py"):
            q = os.path.split(q_path)[1][:-3]
            result = grader.check(q) #global_env=global_env)
            if q != "q2":
                self.assertEqual(result.grade, 1, f"Test {q} expected to pass but failed:\n{result}")
            else:
                self.assertEqual(result.grade, 0, f"Test {q} expected to fail but passed:\n{result}")
    
    def test_check_all_repr(self):
        """
        Checks that the representation of results as strings is correct
        """
        grader = Notebook(TEST_FILES_PATH + "tests")

        output = str(grader.check_all())

        # checks each question substring 
        output_lst = [
            'q1:\n\n    All tests passed!\n',
            'q2:\n\n    \n    0 of 1 tests passed\n',
            'q3:\n\n    All tests passed!\n',
            'q4:\n\n    All tests passed!\n',
            'q5:\n\n    All tests passed!\n'
        ]

        for result in output_lst:
            self.assertTrue(output.count(result) == 1)

    def test_export(self):
        """
        Checks export contents for existence of PDF and equality of zip
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.export(TEST_FILES_PATH + "test-nb.ipynb", filtering=False)

        self.assertTrue(os.path.isfile(TEST_FILES_PATH + "test-nb.pdf"))
        
        with self.unzip_to_temp(TEST_FILES_PATH + "test-nb.zip") as unzipped_dir:
            # breakpoint()
            self.assertDirsEqual(
                unzipped_dir, 
                TEST_FILES_PATH + "export-correct", 
                ignore_ext=[".pdf", ""] # second ignores .OTTER_LOG files
            )

        # cleanup
        os.remove(TEST_FILES_PATH + "test-nb.pdf")
        os.remove(TEST_FILES_PATH + "test-nb.zip")

    @patch.object(LogEntry, "shelve")
    def test_nb_log(self, mock_log):
        """
        Checks existence of log when running nb
        """

        mock_log.return_value = LogEntry(EventType.CHECK)
        grader = Notebook(TEST_FILES_PATH + "tests")
        output = grader.check_all()

        self.assertTrue(os.path.isfile(_OTTER_LOG_FILENAME))
    
    def tearDown(self):
        if os.path.isfile(_OTTER_LOG_FILENAME):
            os.remove(_OTTER_LOG_FILENAME)
