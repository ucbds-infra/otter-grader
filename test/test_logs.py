################################
##### Tests for Otter Logs #####
################################

import os
import unittest

from otter.check.logs import Log
from otter.check.notebook import Notebook, _OTTER_LOG_FILENAME
from otter.check.logs import LogEntry, EventType, Log
from . import TestCase

import numpy as np
from sklearn.linear_model import LinearRegression
import sys

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test-logs/"

class TestLogs(TestCase):

    grading_results = {}
    entry_results = {}
    test_directory = TEST_FILES_PATH + "tests"

    def setUp(self):
        super().setUp()
        self.grading_results = {}
        self.entry_results = {}
        self.maxDiff = None

    def test_Notebook_check(self):
        grader = Notebook(self.test_directory)

        def square(x):
            return x**2

        for test_file in os.listdir(self.test_directory):
            if os.path.splitext(test_file)[1] != ".py":
                continue
            test_name = os.path.splitext(test_file)[0]
            self.grading_results[test_name] = grader.check(test_name)

        log = Log.from_file(_OTTER_LOG_FILENAME)

        for question in log.get_questions():
            logged_result = log.get_results(question)
            actual_result = self.grading_results[question]

            # checking repr since the results __eq__ method is not defined
            self.assertEqual(repr(logged_result), repr(actual_result), f"Logged results for {question} are not correct")


    def test_grade_check(self):
        grader = Notebook(self.test_directory)

        def square(x):
            return x**2
        
        for test_file in os.listdir(self.test_directory):
            if os.path.splitext(test_file)[1] != ".py":
                continue
            test_name = os.path.splitext(test_file)[0]
            self.grading_results[test_name] = grader.check(test_name)

        log = Log.from_file(_OTTER_LOG_FILENAME)

        for question in log.get_questions():
            logged_grade = log.get_question_entry(question).get_score_perc()
            actual_grade = self.grading_results[question].grade
<<<<<<< HEAD
=======

            # checking repr since the results __eq__ method is not defined
>>>>>>> cd5d569a47f3087b6423bc8932818631b7c2b92f
            self.assertEqual(logged_grade, actual_grade, f"Logged results for {question} are not correct")


    def test_question_entry(self):
        grader = Notebook(self.test_directory)

        def square(x):
            return x**2

        for test_file in os.listdir(self.test_directory):
            if os.path.splitext(test_file)[1] != ".py":
                continue
            test_name = os.path.splitext(test_file)[0]
            self.entry_results[test_name] = grader.check(test_name)

        log = Log.from_file(_OTTER_LOG_FILENAME)

        for question in log.get_questions():
            logged_result = log.get_question_entry(question).get_results()
            actual_result = self.entry_results[question]

            # checking repr since the results __eq__ method is not defined
            self.assertEqual(repr(logged_result), repr(actual_result), f"Logged results for {question} are not correct")

    def test_shelve(self):
        # tests shelve() and unshelve() which call shelve_environment()

        def square(x):
            return x**2
        env = {"num": 5, "func": square, "model": LinearRegression(), "module": sys}

        #from otter.logs import LogEntry
        entry = LogEntry(
            event_type=EventType.AUTH,
            results=[],
            question=None, 
            success=True, 
            error=None
        )

        #ignore modules test
 

        entry.shelve(env, delete=True, filename = _OTTER_LOG_FILENAME)
        self.assertTrue(entry.shelf)
        self.assertEqual(entry.unshelved, ["module"])

        entry.flush_to_file(_OTTER_LOG_FILENAME) 

        from math import factorial

        log = Log.from_file(_OTTER_LOG_FILENAME)
        env = entry.unshelve()
        self.assertEqual([*env], ["num", "func", "model"])

        env_with_factorial = entry.unshelve(dict(factorial = factorial ))
        self.assertTrue("factorial" in env_with_factorial["square"].__globals__)
        self.assertTrue(factorial is env_with_factorial["square"].__globals__["factorial"])


    
    
    # def test_Log_getItem(self):
    #     entry = LogEntry(

    #     )
    #     #log = Log.from_file(_OTTER_LOG_FILENAME)

    #     assertEqual(log.__repr__(), "otter.logs.Log([\n  {}\n])".format(",\n  ".join([repr(e) for e in self.entries])))

    #     def square(x):
    #         return x**2

    #     log = Log.from_file(_OTTER_LOG_FILENAME)

    #     entry1 = log.__getitem__(0)
    #     #assert entry1 == 

    # def test_Log_iter(self):
    #     #log = Log.from_file(_OTTER_LOG_FILENAME, ascending = True)
    #     #list of entries
    #     #logIter = log.iter()
    #     logIter = log.question_iterator() #most recent entries / question
    #     nextLog = next(logIter) 
    #     #assert nextLog == 




    # def test_shelve_environment(self):
    #     env = 
    #     entry = LogEntry()
    #     picled_env = entry.shelve_environment(env)[0]
    #     enshelved = entry.shelve_environment(env)[1]


# log.questions_iterator

#repr, sort, 

    def tearDown(self):
        if os.path.isfile(_OTTER_LOG_FILENAME):
            os.remove(_OTTER_LOG_FILENAME)