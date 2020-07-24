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
from otter.logs import LogEntry, EventType, Log

from otter import Notebook
from otter.notebook import _OTTER_LOG_FILENAME

TEST_FILES_PATH = "test/test-notebook/"

def square(x):
    return x**2

def negate(x):
    return not x

class TestNotebook(unittest.TestCase):
# https://otter-grader.readthedocs.io/en/beta/otter_check.html notebook
# add'l test for Notebook.check -- call where you don't pass in a global env -- just pass the test file path  - debugging

# check that to_pdf creates PDF -- not sure how to check for accuracy - bibtex error 

# check that export makes zip w/ correct contents - check in

    def check_zipfile(self, path, correct_dir_path, files=[]):
        # unzip the zipfile
        unzip_command = ["unzip", path, "-d", TEST_FILES_PATH + "export"]
        unzip = subprocess.run(unzip_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(unzip.stderr), 0, unzip.stderr.decode("utf-8"))

        # TODO : file pathing is hack for now (unzipping doesn't work)
        self.assertDirsEqual(TEST_FILES_PATH + "export" + TEST_FILES_PATH, correct_dir_path, ignore_ext=[".pdf"])

        # cleanup
        if os.path.exists(TEST_FILES_PATH + "export"):
            shutil.rmtree(TEST_FILES_PATH + "export")

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

    def test_nb_class_no_env(self):
        """
        Checks that the otter.Notebook class works correctly, with no global env input
        """
        grader = Notebook(TEST_FILES_PATH + "tests")

        

        #global_env = {
        #    "square" : square,
        #    "negate" : negate
        #}

        for q_path in glob(TEST_FILES_PATH + "tests/*.py"):
            q = os.path.split(q_path)[1][:-3]
            result = grader.check(q) #global_env=global_env)
            if q != "q2":
                self.assertEqual(result.grade, 1, f"Test {q} expected to pass but failed:\n{result}")
            else:
                self.assertEqual(result.grade, 0, f"Test {q} expected to fail but passed:\n{result}")
    
    def test_checkall_repr(self):
        """
        Checks correct output for the OKTestsDisplay via check_all
        """
        grader = Notebook(TEST_FILES_PATH + "tests")

        def square(x):
            return x**2

        def negate(x):
            return not x

        output = str(grader.check_all())
        # checks each question substring 
        output_lst = [
            'q1:\n\n    All tests passed!\n',
            'q2:\n\n    \n    0 of 1 tests passed\n',
            'q3:\n\n    All tests passed!\n',
            'q4:\n\n    All tests passed!\n',
            'q5:\n\n    All tests passed!\n'
            #'q4:\n\n    \n    0 of 1 tests passed',
            #'q5:\n\n    \n    0 of 1 tests passed'
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
        self.check_zipfile(
                    TEST_FILES_PATH + "test-nb.zip", TEST_FILES_PATH + "correct/test-nb", 
                    ["test-nb.pdf","test-nb.ipynb"]
                )
        cleanup_command = ["rm", TEST_FILES_PATH + "test-nb.pdf", TEST_FILES_PATH + "test-nb.zip"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(cleanup.returncode, 0,"Error in cleanup:" + str(cleanup.stderr))

    @patch.object(LogEntry,"shelve")
    def test_nb_log(self, mock_log):
        """
        Checks existence of log when running nb
        """

        mock_log.return_value = LogEntry(EventType.CHECK)
        grader = Notebook(TEST_FILES_PATH + "tests")
        output = grader.check_all()

        # f = open("demofile2.txt", "a")
        # f.write("\n" + os.getcwd() + "nb_log:\n")
        # f.close()

        self.assertTrue(os.path.isfile(".OTTER_LOG"))
    
    def tearDown(self):
        if os.path.isfile(_OTTER_LOG_FILENAME):
            os.remove(_OTTER_LOG_FILENAME)
