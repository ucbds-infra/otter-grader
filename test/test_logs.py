################################
##### Tests for Otter Logs #####
################################

import os
import unittest

from otter.argparser import get_parser
from otter.check.logs import Log
from otter.check.notebook import Notebook, _OTTER_LOG_FILENAME
from otter.check.logs import LogEntry, EventType, Log
from . import TestCase

import numpy as np
from sklearn.linear_model import LinearRegression
import sys

parser = get_parser()

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
        grader = Notebook(test_dir=self.test_directory)

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
        grader = Notebook(test_dir=self.test_directory)

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

            # checking repr since the results __eq__ method is not defined
            self.assertEqual(logged_grade, actual_grade, f"Logged results for {question} are not correct")

    def test_question_entry(self):
        grader = Notebook(test_dir=self.test_directory)

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

        import calendar 

        env = {"num": 5, "func": square, "model": LinearRegression(), "module": sys, "ignored_func": calendar.setfirstweekday}

     
        entry = LogEntry(
            event_type=EventType.AUTH,
            results=[],
            question=None, 
            success=True, 
            error=None
        )
 

        entry.shelve(env, delete=True, filename = _OTTER_LOG_FILENAME, ignore_modules=['calendar'])
        self.assertTrue(entry.shelf)
        self.assertEqual(entry.unshelved, ["module", "ignored_func"])

        entry.flush_to_file(_OTTER_LOG_FILENAME) 

        from math import factorial

        log = Log.from_file(_OTTER_LOG_FILENAME)
        env = entry.unshelve()
        self.assertEqual([*env], ["num", "func", "model"])

        env_with_factorial = entry.unshelve(dict(factorial = factorial ))
        self.assertTrue("factorial" in env_with_factorial["func"].__globals__)
        self.assertTrue(factorial is env_with_factorial["func"].__globals__["factorial"])
    
    def test_Log_getItem(self):
        entry1 = LogEntry(
            event_type=EventType.AUTH,
            results=[],
            question=None, 
            success=True, 
            error=None
        )

        entry1.flush_to_file(_OTTER_LOG_FILENAME)

        log = Log.from_file(_OTTER_LOG_FILENAME)

        self.assertEqual(log.__getitem__(0).event_type, entry1.event_type)
        

    def test_Log_iter(self):
        #log = Log.from_file(_OTTER_LOG_FILENAME, ascending = True)
        #list of entries
        #logIter = log.iter()

        entry1 = LogEntry(
            event_type=EventType.CHECK,
            results=[],
            question= "q1", 
            success=True, 
            error=None
        )

        entry2 = LogEntry(
            event_type=EventType.CHECK,
            results=[],
            question= "q1", 
            success=True, 
            error=None
        )

        entry3 = LogEntry(
            event_type=EventType.CHECK,
            results=[],
            question= "q2", 
            success=True, 
            error=None
        )

        entry1.flush_to_file(_OTTER_LOG_FILENAME)
        entry2.flush_to_file(_OTTER_LOG_FILENAME)
        entry3.flush_to_file(_OTTER_LOG_FILENAME)

        log = Log.from_file(_OTTER_LOG_FILENAME)

        logIter = log.question_iterator() #most recent entries / question
        self.assertEqual(logIter.questions , ["q1", "q2"])

        nextLogEntry = next(logIter)

        self.assertEqual(nextLogEntry.question, entry2.question)

        nextLogEntry = next(logIter)

        self.assertEqual(nextLogEntry.question, entry3.question)

    def tearDown(self):
        if os.path.isfile(_OTTER_LOG_FILENAME):
            os.remove(_OTTER_LOG_FILENAME)
