##################################
##### Tests for otter notebook #####
##################################

import unittest
import sys
import os
import shutil
import subprocess
import responses


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
    return x ** 2


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
            return x ** 2

        def negate(x):
            return not x

        global_env = {
            "square": square,
            "negate": negate
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
            result = grader.check(q)  # global_env=global_env)
            if q != "q2":
                self.assertEqual(result.grade, 1, f"Test {q} expected to pass but failed:\n{result}")
            else:
                self.assertEqual(result.grade, 0, f"Test {q} expected to fail but passed:\n{result}")

    def test_check_raise_exception(self):
        """
        Checks that the otter.Notebook class check method correctly raises Exceptions
        when things go wrong
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        global_env = 0
        for q_path in glob(TEST_FILES_PATH + "tests/*.py"):
            q = os.path.split(q_path)[1][:-3]
            self.assertRaises(AttributeError,
                              lambda: grader.check(q, global_env=global_env))

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

    def test_to_pdf_with_nb_path(self):
        """
        Checks for existence of notebook PDF
        This test is the general use case WITH a specified notebook path
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.to_pdf(TEST_FILES_PATH + "test-nb.ipynb", filtering=False)

        self.assertTrue(os.path.isfile(TEST_FILES_PATH + "test-nb.pdf"))
        # cleanup
        os.remove(TEST_FILES_PATH + "test-nb.pdf")

    def test_to_pdf_without_nb_path_case1_pass(self):
        """
        Checks for the existence of notebook PDF
        This test is for the case where notebook path is not defined,
        but there exists a .otter file specifing the IPYNB notebook name
        """
        responses.add(responses.GET, 'http://some.url/auth/google',
                      json={'Key': '1234125'}, status=404)
        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.to_pdf(nb_path = None, filtering=False)
        self.assertTrue(os.path.exists("test-nb.pdf"))
        # cleanup
        os.remove("test-nb.pdf")

    def test_to_pdf_without_nb_path_case2_fail(self):
        """
        Checks for correct error scenario for to_pdf method
        This test is for when np_path is set to None and multiple
        IPYNB notebooks exist in the working directory.
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        self.assertRaises(AssertionError,
                          lambda: grader.to_pdf(nb_path=None, filtering=False))

    def test_to_pdf_without_nb_path_case2_pass(self):
        """
        Checks for correct scenario on to_pdf method
        This test is for when np_path is set to None and only 1
        IPYNB notebook exists in the working directory.
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.to_pdf(nb_path=None, filtering = False)

        self.assertTrue(os.path.exists("test-nb.pdf"))
        # cleanup
        os.remove("test-nb.pdf")

    def test_to_pdf_without_nb_path_case3(self):
        """
        Checks for correct error scenario for to_pdf method
        This test is for when nb_path is set to None, should raise ValueError
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        self.assertRaises(ValueError,
                          lambda: grader.to_pdf(nb_path=None, filtering=False))

    def test_export_without_nb_path_case2_pass(self):
        """
        Checks for correct error scenario for export method
        This test is for when nb_path is set to None and
        there is only 1 IPYNB notebook in working directory
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.export(nb_path=None, filtering=False)

        self.assertTrue(os.path.isfile("test-nb.pdf"))
        with self.unzip_to_temp("test-nb.zip") as unzipped_dir:
            # breakpoint()
            self.assertDirsEqual(
                unzipped_dir,
                TEST_FILES_PATH + "export-correct/test/test-notebook",
                ignore_ext=[".pdf", ""]  # second ignores .OTTER_LOG files
            )
        # cleanup
        os.remove("test-nb.pdf")
        os.remove("test-nb.zip")

    def test_export_without_nb_path_case2_fail(self):
        """
        Checks for correct error scenario for export method
        This test is for when nb_path is set to None and
        there are multiple IPYNB notebooks in working directory
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        self.assertRaises(AssertionError,
                          lambda: grader.export(nb_path=None, filtering=False))

    def test_export_without_nb_path_case3(self):
        """
        Checks for correct error scenario for export method
        This test is for when nb_path is set to None and
        there are no IPYNB notebooks in the working directory
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        self.assertRaises(ValueError,
                          lambda: grader.export(nb_path=None, filtering=False))

    def test_export_no_error(self):
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
                ignore_ext=[".pdf", ""]  # second ignores .OTTER_LOG files
            )

        # cleanup
        os.remove(TEST_FILES_PATH + "test-nb.pdf")
        os.remove(TEST_FILES_PATH + "test-nb.zip")

    def test_export_multiple_otter_error(self):
        """
        Checks export for error scenario for export method
        This test should pass when export successfully raises an
        AssertionError for the case when the directory contains
        multiple .otter files.
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        self.assertRaises(AssertionError,
                          lambda: grader.export(nb_path=None, filtering=False))

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
