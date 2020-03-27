##################################
##### Tests for otter assign #####
##################################

import unittest
import os
import shutil

from otter.utils import block_print, enable_print

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test-assign/"

class TestAssign(unittest.TestCase):
    
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
        block_print()
        args.func(args)
        enable_print()

        # check that we have the correct output contents
        self.assertTrue(os.path.isdir(TEST_FILES_PATH + "output"))
        self.assertEqual(os.listdir(TEST_FILES_PATH + "output"), ["autograder", "student"])

        # check contents of autograder directory
        self.assertEqual(len(os.listdir(TEST_FILES_PATH + "output/autograder")), 3)
        for f in ["tests", "data.csv", "example.ipynb"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output/autograder"))
        for f in ["q1H.py", "q1.py", "q3.py"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output/autograder/tests"))

        for file in ["example.ipynb", "data.csv", "tests/q1.py", "tests/q1H.py", "tests/q3.py"]:
            with open(os.path.join(TEST_FILES_PATH + "output-correct/autograder", file)) as f:
                correct_contents = f.read()
            with open(os.path.join(TEST_FILES_PATH + "output/autograder", file)) as f:
                contents = f.read()
            self.assertEqual(correct_contents, contents, "Autograder file {} incorrect".format(file))
        
        # check contents of student directory
        self.assertEqual(len(os.listdir(TEST_FILES_PATH + "output/student")), 3)
        for f in ["tests", "data.csv", "example.ipynb"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output/student"))
        for f in ["q1.py", "q3.py"]:
            self.assertIn(f, os.listdir(TEST_FILES_PATH + "output/student/tests"))

        for file in ["example.ipynb", "data.csv", "tests/q1.py", "tests/q3.py"]:
            with open(os.path.join(TEST_FILES_PATH + "output-correct/student", file)) as f:
                correct_contents = f.read()
            with open(os.path.join(TEST_FILES_PATH + "output/student", file)) as f:
                contents = f.read()
            self.assertEqual(correct_contents, contents, "Student file {} incorrect".format(file))
        
        # cleanup the output
        shutil.rmtree(TEST_FILES_PATH + "output")
        