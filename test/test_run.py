###############################
##### Tests for otter run #####
###############################

import os
import unittest
import subprocess
import json
import shutil
import nbformat
import nbconvert

from subprocess import PIPE
from glob import glob
from unittest import mock
from shutil import copyfile

# from otter.argparser import get_parser
from otter.generate.autograder import main as autograder
from otter.run.run_autograder import main as run_autograder

from . import TestCase

# parser = get_parser()

NBFORMAT_VERSION = 4
TEST_FILES_PATH = "test/test-run/"

class TestRun(TestCase):
    def setUp(self):
        super().setUp()

        self.cwd = os.getcwd()

        with open(TEST_FILES_PATH + "autograder/source/otter_config.json") as f:
            self.config = json.load(f)
        
        self.expected_results = {
            "tests": [
                {
                    "name": "q1 - 1",
                    "score": 0.0,
                    "max_score": 0.0,
                    "visibility": "visible",
                    "output": "Test case passed!"
                },
                {
                    "name": "q1 - 2",
                    "score": 0.0,
                    "max_score": 0.0,
                    "visibility": "visible",
                    "output": "Test case passed!"
                },
                {
                    "name": "q1 - 3",
                    "score": 0.0,
                    "max_score": 0.0,
                    "visibility": "hidden",
                    "output": "Test case passed!"
                },
                {
                    "name": "q1 - 4",
                    "score": 0.0,
                    "max_score": 0.0,
                    "visibility": "hidden",
                    "output": "Test case passed!"
                },
                {
                    "name": "q2 - 1",
                    "score": 0.0,
                    "max_score": 0.5,
                    "visibility": "visible",
                    "output": "Trying:\n    negate(True)\nExpecting:\n    False\n**********************************************************************\nLine 2, in q2 0\nFailed example:\n    negate(True)\nExpected:\n    False\nGot:\n    True\n"
                },
                {
                    "name": "q2 - 2",
                    "score": 0.0,
                    "max_score": 0.5,
                    "visibility": "visible",
                    "output": "Trying:\n    negate(False)\nExpecting:\n    True\n**********************************************************************\nLine 2, in q2 1\nFailed example:\n    negate(False)\nExpected:\n    True\nGot:\n    False\n"
                },
                {
                    "name": "q2 - 3",
                    "score": 0.0,
                    "max_score": 0.5,
                    "visibility": "hidden",
                    "output": "Trying:\n    negate(\"\")\nExpecting:\n    True\n**********************************************************************\nLine 2, in q2 2\nFailed example:\n    negate(\"\")\nExpected:\n    True\nGot:\n    ''\n"
                },
                {
                    "name": "q2 - 4",
                    "score": 0.0,
                    "max_score": 0.5,
                    "visibility": "hidden",
                    "output": "Trying:\n    negate(1)\nExpecting:\n    False\n**********************************************************************\nLine 2, in q2 3\nFailed example:\n    negate(1)\nExpected:\n    False\nGot:\n    1\n"
                },
                {
                    "name": "q3 - 1",
                    "score": 1.0,
                    "max_score": 1.0,
                    "visibility": "visible",
                    "output": "Test case passed!"
                },
                {
                    "name": "q3 - 2",
                    "score": 1.0,
                    "max_score": 1.0,
                    "visibility": "hidden",
                    "output": "Test case passed!"
                },
                {
                    "name": "q4 - 1",
                    "score": 1.0,
                    "max_score": 1.0,
                    "visibility": "hidden",
                    "output": "Test case passed!"
                },
                {
                    "name": "q6 - 1",
                    "score": 2.5,
                    "max_score": 2.5,
                    "visibility": "visible",
                    "output": "Test case passed!"
                },
                {
                    "name": "q6 - 2",
                    "score": 0.0,
                    "max_score": 2.5,
                    "visibility": "hidden",
                    "output": "Trying:\n    fib = fiberator()\nExpecting nothing\nok\nTrying:\n    for _ in range(10):\n        print(next(fib))\nExpecting:\n    0\n    1\n    1\n    2\n    3\n    5\n    8\n    13\n    21\n    34\n**********************************************************************\nLine 3, in q6 1\nFailed example:\n    for _ in range(10):\n        print(next(fib))\nExpected:\n    0\n    1\n    1\n    2\n    3\n    5\n    8\n    13\n    21\n    34\nGot:\n    0\n    1\n    1\n    1\n    2\n    3\n    5\n    8\n    13\n    21\n"
                },
                {
                    "name": "q7 - 1",
                    "score": 1.0,
                    "max_score": 1.0,
                    "visibility": "visible",
                    "output": "Test case passed!"
                }
            ],
            "output": "Students are allowed 1 submissions every 1 days. You have 0 submissions in that period."
        }

    def test_notebook(self):

        run_autograder(self.config['autograder_dir'])

        with open(TEST_FILES_PATH + "autograder/results/results.json") as f:
            actual_results = json.load(f)

        self.assertEqual(actual_results, self.expected_results, f"Actual results did not matched expected:\n{actual_results}")

    def test_script(self):

        nb_path = TEST_FILES_PATH + "autograder/submission/fails2and6H.ipynb"
        nb = nbformat.read(nb_path, as_version=NBFORMAT_VERSION)
        os.remove(nb_path)

        try:
            py, _ = nbconvert.export(nbconvert.PythonExporter, nb)
            
            # remove magic commands
            py = "\n".join(l for l in py.split("\n") if not l.startswith("get_ipython"))
            
            with open(TEST_FILES_PATH + "autograder/submission/fails2and6H.py", "w+") as f:
                f.write(py)

            run_autograder(self.config['autograder_dir'])

            with open(TEST_FILES_PATH + "autograder/results/results.json") as f:
                actual_results = json.load(f)

            self.assertEqual(actual_results, self.expected_results, f"Actual results did not matched expected:\n{actual_results}")

            self.deletePaths([TEST_FILES_PATH + "autograder/submission/fails2and6H.py"])

            with open(nb_path, "w+") as f:
                nbformat.write(nb, f)
        
        except:
            os.chdir(self.cwd)
            self.deletePaths([TEST_FILES_PATH + "autograder/submission/fails2and6H.py"])
            with open(nb_path, "w+") as f:
                nbformat.write(nb, f)
            
            raise

    def tearDown(self):
        os.chdir(self.cwd)
        self.deletePaths([
            TEST_FILES_PATH + "autograder/results/results.json",
            TEST_FILES_PATH + "autograder/results/results.pkl",
            TEST_FILES_PATH + "autograder/__init__.py",
            TEST_FILES_PATH + "autograder/submission/test",
            TEST_FILES_PATH + "autograder/submission/tests",
            TEST_FILES_PATH + "autograder/submission/__init__.py",
            TEST_FILES_PATH + "autograder/submission/.OTTER_LOG",
        ])
