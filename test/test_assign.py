##################################
##### Tests for otter assign #####
##################################

import unittest
import os
import shutil
import subprocess

from subprocess import PIPE
from glob import glob

from otter.utils import block_print

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test-assign/"

class TestAssign(unittest.TestCase):

    def check_gradescope_zipfile(self, path, config, tests=[], files=[]):
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
            self.assertEqual(run_autograder_globals[k], v, 
                f"Expected config value for {k} ({v}) does not match actual value ({run_autograder_globals[k]})"
            )
    
    def test_convert_example(self):
        """
        Checks that otter assign filters and outputs correctly
        """
        # run otter assign
        run_assign_args = [
            "assign", "--no-run-tests", TEST_FILES_PATH + "example.ipynb", TEST_FILES_PATH + "output", TEST_FILES_PATH + "data.csv"
        ]
        args = parser.parse_args(run_assign_args)

        # block stdout while running
        with block_print():
            args.func(args)

        # check that we have the correct output contents
        self.assertTrue(os.path.isdir(TEST_FILES_PATH + "output"))
        self.assertEqual(os.listdir(TEST_FILES_PATH + "output"), ["autograder", "student"])

        # check contents of autograder directory
        self.assertEqual(len(os.listdir(TEST_FILES_PATH + "output/autograder")), 4)
        for f in ["tests", "data.csv", "example.ipynb", "requirements.txt"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output/autograder"))
        for f in ["q1.py", "q3.py", "q8.py"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output/autograder/tests"))

        for file in ["example.ipynb", "data.csv", "requirements.txt", "tests/q1.py", "tests/q3.py", "tests/q8.py"]:
            with open(os.path.join(TEST_FILES_PATH + "output-correct/autograder", file)) as f:
                correct_contents = f.read()
            with open(os.path.join(TEST_FILES_PATH + "output/autograder", file)) as f:
                contents = f.read()
            self.assertEqual(correct_contents, contents, "Autograder file {} incorrect".format(file))
        
        # check contents of student directory
        self.assertEqual(len(os.listdir(TEST_FILES_PATH + "output/student")), 3)
        for f in ["tests", "data.csv", "example.ipynb"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output/student"))
        for f in ["q1.py", "q3.py", "q8.py"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output/student/tests"))

        for file in ["example.ipynb", "data.csv", "tests/q1.py", "tests/q3.py", "tests/q8.py"]:
            with open(os.path.join(TEST_FILES_PATH + "output-correct/student", file)) as f:
                correct_contents = f.read()
            with open(os.path.join(TEST_FILES_PATH + "output/student", file)) as f:
                contents = f.read()
            self.assertEqual(correct_contents, contents, "Student file {} incorrect".format(file))
        
        # cleanup the output
        shutil.rmtree(TEST_FILES_PATH + "output")

        
    def test_jassign_format_convert_example(self):
        """
        Checks that otter assign --jassign filters and outputs correctly
        """
        # run otter assign
        run_assign_args = [
            "assign", "--no-run-tests", TEST_FILES_PATH + "jassign-example.ipynb", TEST_FILES_PATH + "output-jassign", TEST_FILES_PATH + "data.csv"
        ]
        args = parser.parse_args(run_assign_args)

        # block stdout while running
        with block_print():
            args.func(args)

        # check that we have the correct output contents
        self.assertTrue(os.path.isdir(TEST_FILES_PATH + "output-jassign"))
        self.assertEqual(os.listdir(TEST_FILES_PATH + "output-jassign"), ["autograder", "student"])

        # check contents of autograder directory
        self.assertEqual(len(os.listdir(TEST_FILES_PATH + "output-jassign/autograder")), 4)
        for f in ["tests", "data.csv", "jassign-example.ipynb"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output-jassign/autograder"))
        for f in ["q1.py", "q3.py"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output-jassign/autograder/tests"))

        for file in ["jassign-example.ipynb", "data.csv", "tests/q1.py", "tests/q3.py"]:
            with open(os.path.join(TEST_FILES_PATH + "output-jassign-correct/autograder", file)) as f:
                correct_contents = f.read()
            with open(os.path.join(TEST_FILES_PATH + "output-jassign/autograder", file)) as f:
                contents = f.read()
            self.assertEqual(correct_contents, contents, "Autograder file {} incorrect".format(file))
        
        # check contents of student directory
        self.assertEqual(len(os.listdir(TEST_FILES_PATH + "output-jassign/student")), 3)
        for f in ["tests", "data.csv", "jassign-example.ipynb"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output-jassign/student"))
        for f in ["q1.py", "q3.py"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output-jassign/student/tests"))

        for file in ["jassign-example.ipynb", "data.csv", "tests/q1.py", "tests/q3.py"]:
            with open(os.path.join(TEST_FILES_PATH + "output-jassign-correct/student", file)) as f:
                correct_contents = f.read()
            with open(os.path.join(TEST_FILES_PATH + "output-jassign/student", file)) as f:
                contents = f.read()
            self.assertEqual(correct_contents, contents, "Student file {} incorrect".format(file))
        
        # cleanup the output
        shutil.rmtree(TEST_FILES_PATH + "output-jassign")
        