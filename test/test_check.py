#################################
##### Tests for otter check #####
#################################

import os
import unittest
import subprocess
import contextlib

from textwrap import dedent
from subprocess import PIPE
from glob import glob
from io import StringIO
from unittest import mock

from otter import Notebook
# from otter.argparser import get_parser
from otter.check import main as check
from otter.runner import run_otter

from . import TestCase

# parser = get_parser()

TEST_FILES_PATH = "test/test-check/"

class TestCheck(TestCase):

    def test_otter_check_script(self):
        """
        Checks that the script checker works
        """
        # run for each individual test
        for file in glob(TEST_FILES_PATH + "tests/*.py"):
            check_command = ["check",
                TEST_FILES_PATH + "file0.py", 
                "-q", os.path.split(file)[1][:-3],
                "-t", os.path.split(file)[0]
            ]
            # args = parser.parse_args(check_command)
            # args.func = check

            # capture stdout
            output = StringIO()
            with contextlib.redirect_stdout(output):

                # mock block_print otherwise they interfere with capture of stdout
                with mock.patch("otter.check.block_print"):
                    # args.func(args)
                    run_otter(check_command)
                    if os.path.split(file)[1] != "q2.py":
                        self.assertEqual(
                            output.getvalue().strip().split("\n")[-1].strip(), 
                            "All tests passed!", 
                            "Did not pass test at {}".format(file)
                        )

        # run checker command
        check_command = ["check",
            TEST_FILES_PATH + "file0.py", 
            "-t", TEST_FILES_PATH + "tests"
        ]
        # args = parser.parse_args(check_command)
        # args.func = check

        # capture stdout
        output = StringIO()
        with contextlib.redirect_stdout(output):

            # mock block_print otherwise they interfere with capture of stdout
            with mock.patch("otter.check.block_print"):
                run_otter(check_command)
                self.assertEqual(
                    output.getvalue().strip(), 
                    dedent("""\
                        [0.         0.02002002 0.04004004 0.06006006 0.08008008]
                        q1 results: All test cases passed!
                        q2 results:
                            q2 - 1 result:
                                Trying:
                                    1 == 1
                                Expecting:
                                    False
                                **********************************************************************
                                Line 2, in q2 0
                                Failed example:
                                    1 == 1
                                Expected:
                                    False
                                Got:
                                    True

                            q2 - 2 result:
                                Test case passed!
                        q3 results: All test cases passed!
                        q4 results: All test cases passed!
                        q5 results: All test cases passed!"""), 
                    "Did not pass correct tests"
                )


    def test_otter_check_notebook(self):
        """
        Checks that the script checker works
        """
        # run for each individual test
        for file in glob(TEST_FILES_PATH + "tests/*.py"):
            check_command = ["check",
                TEST_FILES_PATH + "test-nb.ipynb", 
                "-q", os.path.split(file)[1][:-3],
                "-t", os.path.split(file)[0]
            ]
            # args = parser.parse_args(check_command)
            # args.func = check

            # capture stdout
            output = StringIO()
            with contextlib.redirect_stdout(output):

                # mock block_print otherwise they interfere with capture of stdout
                with mock.patch("otter.check.block_print"):
                    # args.func(args)
                    run_otter(check_command)
                    if os.path.split(file)[1] != "q2.py":
                        self.assertEqual(
                            output.getvalue().strip().split("\n")[-1].strip(), 
                            "All tests passed!", 
                            "Did not pass test at {}".format(file)
                        )

        # run checker command
        check_command = ["check",
            TEST_FILES_PATH + "test-nb.ipynb", 
            "-t", TEST_FILES_PATH + "tests"
        ]
        # args = parser.parse_args(check_command)
        # args.func = check

        # capture stdout
        output = StringIO()
        with contextlib.redirect_stdout(output):

        # mock block_print otherwise they interfere with capture of stdout
            with mock.patch("otter.check.block_print"):
                # print(output.getvalue())

                run_otter(check_command)
                self.assertEqual(
                    output.getvalue().strip(), 
                    dedent("""\
                        [0.         0.02002002 0.04004004 0.06006006 0.08008008]
                        q1 results: All test cases passed!
                        q2 results:
                            q2 - 1 result:
                                Trying:
                                    1 == 1
                                Expecting:
                                    False
                                **********************************************************************
                                Line 2, in q2 0
                                Failed example:
                                    1 == 1
                                Expected:
                                    False
                                Got:
                                    True

                            q2 - 2 result:
                                Test case passed!
                        q3 results: All test cases passed!
                        q4 results: All test cases passed!
                        q5 results: All test cases passed!"""), 
                    "Did not pass correct tests"
                )
    
    @classmethod
    def tearDownClass(cls):
        if os.path.exists(".OTTER_LOG"):
            os.system("rm .OTTER_LOG")
