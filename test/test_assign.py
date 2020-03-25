import unittest
import subprocess
import os
import argparse

from subprocess import PIPE

from otter.assign import main

class TestAssign(unittest.TestCase):
    
    def test_convert_example(self):
        assign_parser = argparse.ArgumentParser()
        assign_parser.add_argument("master", help="Notebook with solutions and tests.")
        assign_parser.add_argument("result", help="Directory containing the result.")
        assign_parser.add_argument("--no-export-cell", help="Don't inject an export cell into the notebook", default=False, action="store_true")
        assign_parser.add_argument("--no-run-tests", help="Don't run tests.", default=False, action="store_true")
        assign_parser.add_argument("--no-init-cell", help="Don't automatically generate an Otter init cell", default=False, action="store_true")
        assign_parser.add_argument("--no-check-all", help="Don't automatically add a check_all cell", default=False, action="store_true")
        assign_parser.add_argument("--no-filter", help="Don't filter the PDF.", default=False, action="store_true")
        assign_parser.add_argument("--instructions", help="Additional submission instructions for students")
        assign_parser.add_argument("files", nargs='*', help="Other support files needed for distribution (e.g. .py files, data files)")
        run_oassign_args = ["--no-run-tests", "test/example.ipynb", "test/output", "test/data.csv"]
        main(assign_parser.parse_args(run_oassign_args))

        self.assertTrue(os.path.isdir("test/output"))
        self.assertEqual(os.listdir("test/output"), ["autograder", "student"])

        # check contents of autograder directory
        self.assertEqual(len(os.listdir("test/output/autograder")), 3)
        for f in ["tests", "data.csv", "example.ipynb"]:
            self.assertIn(f, os.listdir("test/output/autograder"))
        for f in ["q1H.py", "q1.py", "q3.py"]:
            self.assertIn(f, os.listdir("test/output/autograder/tests"))

        for file in ["example.ipynb", "data.csv", "tests/q1.py", "tests/q1H.py", "tests/q3.py"]:
            with open(os.path.join("test/output-correct/autograder", file)) as f:
                correct_contents = f.read()
            with open(os.path.join("test/output/autograder", file)) as f:
                contents = f.read()
            self.assertEqual(correct_contents, contents, "Autograder file {} incorrect".format(file))
        
        # check contents of student directory
        self.assertEqual(len(os.listdir("test/output/student")), 3)
        for f in ["tests", "data.csv", "example.ipynb"]:
            self.assertIn(f, os.listdir("test/output/student"))
        for f in ["q1.py", "q3.py"]:
            self.assertIn(f, os.listdir("test/output/student/tests"))

        for file in ["example.ipynb", "data.csv", "tests/q1.py", "tests/q3.py"]:
            with open(os.path.join("test/output-correct/student", file)) as f:
                correct_contents = f.read()
            with open(os.path.join("test/output/student", file)) as f:
                contents = f.read()
            self.assertEqual(correct_contents, contents, "Student file {} incorrect".format(file))
        