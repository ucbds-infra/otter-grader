####################################
##### Tests for otter execute #####
####################################
import os
import unittest
import subprocess
import json
import shutil

from .. import TestCase
TestCase.maxDiff = None
from ast import literal_eval
from otter.execute.results import GradingResults
from otter.test_files.abstract_test import TestCollectionResults, TestFile
from otter.test_files.ok_test import OKTestFile

class TestResults(TestCase):

    """
    results:
    get_score
    _repr_
    to_dict
    get_public_score
    """
    """
    input to grading the class is a list of testCollection objects that are in the docstirng
    """
    def testGetScore(self):
        tests = [OKTestFile("test1", ["t1","t2"],[True,False]), OKTestFile("test2", ["t1","t2"],[True,False],value=0.9,hidden=True)]
        testRes = TestCollectionResults(grade=0.9,paths="test/",tests=tests,passed_tests=tests,failed_tests=[],include_grade=True)
        g = GradingResults([testRes])
        self.assertEqual(g.get_score("test1"), 0.9)

    def testRepr(self):
        tests = [OKTestFile("test1", ["t1","t2"],[True,False]), OKTestFile("test2", ["t1","t2"],[True,False],value=0.9,hidden=True)]
        testRes = TestCollectionResults(grade=0.9,paths="test/",tests=tests,passed_tests=tests,failed_tests=[],include_grade=True)
        g = GradingResults([testRes])
        f = open("demofile2.txt", "a")
        f.write("repr:\n")
        f.write(repr(g))
        f.write("m\nm\nm\n")
        f.close()
        str = "{ 'test1': { 'hidden': False,\n             'incorrect': False,\n             'name': 'test1',\n             'possible': 1,\n             'score': 0.9,\n             'test':    test1\n\nTest result:\nNone},\n  'test2': { 'hidden': False,\n             'incorrect': False,\n             'name': 'test2',\n             'possible': 0.9,\n             'score': 0.81,\n             'test':    test2\n\nTest result:\nNone}}"
        self.assertEqual(repr(g),str)

    def testDict(self):
        tests = [OKTestFile("test1", ["t1","t2"],[True,False]), OKTestFile("test2", ["t1","t2"],[True,False],value=0.9,hidden=False)]
        testRes = TestCollectionResults(grade=0.9,paths="test/",tests=tests,passed_tests=tests,failed_tests=[],include_grade=True)
        g = GradingResults([testRes])
        f = open("demofile2.txt", "a")
        f.write("dict:\n")
        f.write(str(g.to_dict()))
        f.write("m\nm\nm\n")
        f.close()
        d = "{'test1': {'name': 'test1', 'score': 0.9, 'possible': 1, 'test':    test1\n\nTest result:\nNone, 'hidden': False, 'incorrect': False}, 'test2': {'name': 'test2', 'score': 0.81, 'possible': 0.9, 'test':    test2\n\nTest result:\nNone, 'hidden': False, 'incorrect': False}}"
        self.assertEqual(str(g.to_dict()),d)

    def getPublicScore(self):
        tests = [OKTestFile("test1", ["t1","t2"],[True,False]), OKTestFile("test2", ["t1","t2"],[True,False],value=0.9,hidden=False)]
        testRes = TestCollectionResults(grade=0.9,paths="test/",tests=tests,passed_tests=tests,failed_tests=[],include_grade=True)
        g = GradingResults([testRes])
        self.assertEqual(g.get_public_score("test1"), 1)
        self.assertEqual(g.get_public_score("test2"), 0.9)

    def testGradescopeDict(self):
        tests = [OKTestFile("test1", ["t1","t2"],[True,False]), OKTestFile("test2", ["t1","t2"],[True,False],value=0.9,hidden=False)]
        testRes = TestCollectionResults(grade=0.9,paths="test/",tests=tests,passed_tests=tests,failed_tests=[],include_grade=True)
        g = GradingResults([testRes])
        # TODO : multiline this

        gs_dict = "{'tests': [{'name': 'test1 - Public', 'score': 0.0, 'max_score': 0, 'visibility': 'visible', 'output': 'All tests passed!'}, {'name': 'test1 - Hidden', 'score': 0.9, 'max_score': 1, 'visibility': 'hidden', 'output': 'All tests passed!'}, {'name': 'test2 - Public', 'score': 0.0, 'max_score': 0.0, 'visibility': 'visible', 'output': 'All tests passed!'}, {'name': 'test2 - Hidden', 'score': 0.81, 'max_score': 0.9, 'visibility': 'hidden', 'output': 'All tests passed!'}], 'stdout_visibility': 'after_published', 'score': 2}"
        self.assertEqual(str(g.to_gradescope_dict(config={"show_stdout_on_release":True,"score_threshold":0.5,"points_possible":2})), gs_dict)        
