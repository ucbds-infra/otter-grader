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

from otter.run.run_autograder import main as run_autograder

from . import TestCase


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
                    "name": "Public Tests",
                    "visibility": "visible",
                    "output": "q1 results: All test cases passed!\n\nq2 results:\n    q2 - 1 result:\n        Trying:\n            negate(True)\n        Expecting:\n            False\n        **********************************************************************\n        Line 2, in q2 0\n        Failed example:\n            negate(True)\n        Expected:\n            False\n        Got:\n            True\n\n    q2 - 2 result:\n        Trying:\n            negate(False)\n        Expecting:\n            True\n        **********************************************************************\n        Line 2, in q2 1\n        Failed example:\n            negate(False)\n        Expected:\n            True\n        Got:\n            False\n\nq3 results: All test cases passed!\n\nq4 results: All test cases passed!\n\nq6 results: All test cases passed!\n\nq7 results: All test cases passed!"
                },
                {
                    "name": "q1",
                    "score": 0.0,
                    "max_score": 0.0,
                    "visibility": "hidden",
                    "output": "q1 results: All test cases passed!"
                },
                {
                    "name": "q2",
                    "score": 0,
                    "max_score": 2.0,
                    "visibility": "hidden",
                    "output": "q2 results:\n    q2 - 1 result:\n        Trying:\n            negate(True)\n        Expecting:\n            False\n        **********************************************************************\n        Line 2, in q2 0\n        Failed example:\n            negate(True)\n        Expected:\n            False\n        Got:\n            True\n\n    q2 - 2 result:\n        Trying:\n            negate(False)\n        Expecting:\n            True\n        **********************************************************************\n        Line 2, in q2 1\n        Failed example:\n            negate(False)\n        Expected:\n            True\n        Got:\n            False\n\n    q2 - 3 result:\n        Trying:\n            negate(\"\")\n        Expecting:\n            True\n        **********************************************************************\n        Line 2, in q2 2\n        Failed example:\n            negate(\"\")\n        Expected:\n            True\n        Got:\n            ''\n\n    q2 - 4 result:\n        Trying:\n            negate(1)\n        Expecting:\n            False\n        **********************************************************************\n        Line 2, in q2 3\n        Failed example:\n            negate(1)\n        Expected:\n            False\n        Got:\n            1"
                },
                {
                    "name": "q3",
                    "score": 2.0,
                    "max_score": 2.0,
                    "visibility": "hidden",
                    "output": "q3 results: All test cases passed!"
                },
                {
                    "name": "q4",
                    "score": 1.0,
                    "max_score": 1.0,
                    "visibility": "hidden",
                    "output": "q4 results: All test cases passed!"
                },
                {
                    "name": "q6",
                    "score": 2.5,
                    "max_score": 5.0,
                    "visibility": "hidden",
                    "output": "q6 results:\n    q6 - 1 result:\n        Test case passed!\n\n    q6 - 2 result:\n        Trying:\n            fib = fiberator()\n        Expecting nothing\n        ok\n        Trying:\n            for _ in range(10):\n                print(next(fib))\n        Expecting:\n            0\n            1\n            1\n            2\n            3\n            5\n            8\n            13\n            21\n            34\n        **********************************************************************\n        Line 3, in q6 1\n        Failed example:\n            for _ in range(10):\n                print(next(fib))\n        Expected:\n            0\n            1\n            1\n            2\n            3\n            5\n            8\n            13\n            21\n            34\n        Got:\n            0\n            1\n            1\n            1\n            2\n            3\n            5\n            8\n            13\n            21"
                },
                {
                    "name": "q7",
                    "score": 1.0,
                    "max_score": 1.0,
                    "visibility": "hidden",
                    "output": "q7 results: All test cases passed!"
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
