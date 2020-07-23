################################
##### Tests for Otter Logs #####
################################

import os
import unittest

from otter.check.logs import Log
from otter.check.notebook import Notebook, _OTTER_LOG_FILENAME

from . import TestCase

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test-logs/"

class TestLogs(TestCase):

    grading_results = {}

    def setUp(self):
        super().setUp()

        test_files_path = TEST_FILES_PATH + "tests"

        grader = Notebook(test_files_path)

        def square(x):
            return x**2

        for test_file in os.listdir(test_files_path):
            if os.path.splitext(test_file)[1] != ".py":
                continue
            test_name = os.path.splitext(test_file)[0]
            self.grading_results[test_name] = grader.check(test_name)

    def test_something(self):
        log = Log.from_file(_OTTER_LOG_FILENAME)

        for question in log.get_questions():
            logged_result = log.get_results(question)
            actual_result = self.grading_results[question]

            # checking repr since the results __eq__ method is not defined
            self.assertEqual(repr(logged_result), repr(actual_result), f"Logged results for {question} are not correct")

    def tearDown(self):
        if os.path.isfile(_OTTER_LOG_FILENAME):
            os.remove(_OTTER_LOG_FILENAME)
