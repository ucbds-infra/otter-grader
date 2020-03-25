import os
import sys
import unittest
import subprocess
import contextlib
import json
import shutil
import pandas as pd

from textwrap import dedent
from subprocess import PIPE
from glob import glob
from io import StringIO
from unittest import mock

from otter import Notebook

# read in argument parser
with open("bin/otter") as f:
    exec(f.read())

class TestIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        create_image_cmd = ["make", "docker-test"]
        create_image = subprocess.run(create_image_cmd, stdout=PIPE, stderr=PIPE)
        # TestIntegration.assertEqual(len(create_image.stderr), 0, create_image.stderr.decode("utf-8"))

    def test_docker(self):
        """
        Check that we have the right container installed and that docker is running
        """
        # use docker image inspect to see that the image is installed and tagged as otter-grader
        inspect = subprocess.run(["docker", "image", "inspect", "otter-test"], stdout=PIPE, stderr=PIPE)

        # assert that it didn't fail, it will fail if it is not installed
        self.assertEqual(len(inspect.stderr), 0, inspect.stderr.decode("utf-8"))

    def test_hundred_notebooks(self):
        """
        Check that the example of 100 notebooks runs correctely locally.
        """
        # grade the 100 notebooks
        grade_command = ["grade",
            "-y", "test/integration/manual-test/meta.yml", 
            "-p", "test/integration/manual-test/", 
            "-t", "test/integration/tests/", 
            "-r", "test/integration/requirements.txt",
            "-o", "test/",
            "--image", "otter-test"
        ]
        args = parser.parse_args(grade_command)
        args.func(args)
        # grade = subprocess.run(grade_command, stdout=PIPE, stderr=PIPE)

        # assert that otter-grader succesfully ran
        # self.assertEqual(len(grade.stderr), 0, grade.stderr)

        # read the output and expected output
        df_test = pd.read_csv("test/final_grades.csv").sort_values("identifier").reset_index(drop=True)
        df_correct = pd.read_csv("test/integration/final_grades_correct.csv").sort_values("identifier").reset_index(drop=True)

        # assert the dataframes are as expected
        self.assertTrue(df_test.equals(df_correct), "Dataframes not equal")

        # remove the extra output
        cleanup_command = ["rm", "test/final_grades.csv"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)

        # assert cleanup worked
        self.assertEqual(len(cleanup.stderr), 0, "Error in cleanup")

    def test_hundred_scripts(self):
        """
        Check that the example of 100 scripts runs correctely locally.
        """
        # grade the 100 scripts
        grade_command = ["grade",
            "-sy", "test/integration/py-tests/meta.yml", 
            "-p", "test/integration/py-tests/", 
            "-t", "test/integration/tests/", 
            "-r", "test/integration/requirements.txt",
            "-o", "test/",
            "--image", "otter-test"
        ]
        args = parser.parse_args(grade_command)
        args.func(args)
        # grade = subprocess.run(grade_command, stdout=PIPE, stderr=PIPE)

        # assert that otter-grader succesfully ran
        # self.assertEqual(len(grade.stderr), 0, grade.stderr)

        # read the output and expected output
        df_test = pd.read_csv("test/final_grades.csv").sort_values("identifier").reset_index(drop=True)
        df_correct = pd.read_csv("test/integration/final_grades_correct_script.csv").sort_values("identifier").reset_index(drop=True)

        # assert the dataframes are as expected
        self.assertTrue(df_test.equals(df_correct), "Dataframes not equal")

        # remove the extra output
        cleanup_command = ["rm", "test/final_grades.csv"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)

        # assert cleanup worked
        self.assertEqual(len(cleanup.stderr), 0, "Error in cleanup")

    def test_gs_generator(self, cleanup=True):
        """
        Check that the correct zipfile is created by gs_generator.py
        """
        # create the zipfile
        generate_command = ["generate",
            "-t", "test/integration/tests",
            "-o", "test/",
            "-r", "test/integration/requirements.txt",
            "test/integration/test-df.csv"
        ]
        args = parser.parse_args(generate_command)
        args.func(args)
        # gen = subprocess.run(gen_command, stdout=PIPE, stderr=PIPE)

        # assert that otter-grader succesfully ran
        # self.assertEqual(len(gen.stderr), 0, gen.stderr)

        # unzip the zipfile
        unzip_command = ["unzip", "-o", "test/autograder.zip", "-d", "test/autograder"]
        unzip = subprocess.run(unzip_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(unzip.stderr), 0, unzip.stderr)

        # go through files and ensure that they are correct
        for file in glob("test/autograder/*"):
            if os.path.isfile(file):
                correct_file_path = os.path.join("test/integration/autograder-correct", os.path.split(file)[1])
                with open(file) as f:
                    with open(correct_file_path) as g:
                        self.assertEqual(f.read(), g.read(), "{} does not match {}".format(file, correct_file_path))
            else:
                for subfile in glob(os.path.join(file, "*")):
                    correct_file_path = os.path.join("test/integration/autograder-correct", os.path.split(file)[1], os.path.split(subfile)[1])
                    with open(subfile) as f:
                        with open(correct_file_path) as g:
                            self.assertEqual(f.read(), g.read(), "{} does not match {}".format(subfile, correct_file_path))

        # cleanup files
        if cleanup:
            cleanup_command = ["rm", "-rf", "test/autograder", "test/autograder.zip"]
            cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
            self.assertEqual(len(cleanup.stderr), 0, cleanup.stderr.decode("utf-8"))

    def test_gradescope(self):
        """
        Checks that the Gradescope autograder works
        """
        # create the autograder zip file
        self.test_gs_generator(cleanup=False)

        # copy otter-grader dir into test
        shutil.copytree(".", "test/otter-grader")
        shutil.rmtree("test/otter-grader/test")

        # build the docker image
        build = subprocess.run(["docker", "build", "test", "-t", "otter-gradescope-test"], stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(build.stderr), 0, build.stderr.decode("utf-8"))

        # remove the copy of otter-grader
        shutil.rmtree("test/otter-grader")

        # launch the container and return its container ID
        launch = subprocess.run(["docker", "run", "-dt", "otter-gradescope-test", "/autograder/run_autograder"], stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(launch.stderr), 0, launch.stderr.decode("utf-8"))

        # get container ID
        container_id = launch.stdout.decode("utf-8")[:-1]

        # attach to the container and wait for it to finish
        attach = subprocess.run(["docker", "attach", container_id], stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(attach.stderr), 0, attach.stderr.decode("utf-8"))
        
        # copy out the results.json file
        copy = subprocess.run(["docker", "cp", "{}:/autograder/results/results.json".format(container_id), "test/results.json"], stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(copy.stderr), 0, copy.stderr.decode("utf-8"))

        # check that we got the right results
        with open("test/integration/results-correct.json") as f:
            correct_results = json.load(f)
        with open("test/results.json") as f:
            results = json.load(f)
        self.assertEqual(results, correct_results, "Incorrect results when grading in Gradescope container")

        # cleanup files and container
        cleanup = subprocess.run(["rm", "-rf", "test/autograder", "test/autograder.zip", "test/results.json"], stdout=PIPE, stderr=PIPE)
        remove_container = subprocess.run(["docker", "rm", container_id], stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(cleanup.stderr), 0, cleanup.stderr.decode("utf-8"))
        self.assertEqual(len(remove_container.stderr), 0, remove_container.stderr.decode("utf-8"))

    def test_script_checker(self):
        """
        Checks that the script checker works
        """
        # run for each individual test
        for file in glob("test/integration/tests/*.py"):
            check_command = ["check",
                "test/integration/py-tests/file0.py", 
                "-q", os.path.split(file)[1][:-3],
                "-t", os.path.split(file)[0]
            ]
            args = parser.parse_args(check_command)

            # capture stdout
            output = StringIO()
            with contextlib.redirect_stdout(output):

                # mock block_print and enable_print otherwise they interfere with capture of stdout
                with mock.patch("otter.check.block_print"):
                    with mock.patch("otter.check.enable_print"):
                        args.func(args)
                        if os.path.split(file)[1] != "q2.py":
                            self.assertEqual(
                                output.getvalue().strip().split("\n")[-1].strip(), 
                                "All tests passed!", 
                                "Did not pass test at {}".format(file)
                            )

        # run checker command
        check_command = check_command = ["check",
            "test/integration/py-tests/file0.py", 
            "-t", "test/integration/tests"
        ]
        args = parser.parse_args(check_command)

        # capture stdout
        output = StringIO()
        with contextlib.redirect_stdout(output):

            # mock block_print and enable_print otherwise they interfere with capture of stdout
            with mock.patch("otter.check.block_print"):
                with mock.patch("otter.check.enable_print"):
                    args.func(args)
                    self.assertEqual(
                        output.getvalue().strip(), 
                        dedent("""\
                            [0.         0.02002002 0.04004004 0.06006006 0.08008008]
                            4 of 5 tests passed

                            Tests passed:
                             q1  q3  q4  q5 


                            Tests failed: 
                               test/integration/tests/q2.py

                            Test result:
                            Trying:
                                1 == 1
                            Expecting:
                                False
                            **********************************************************************
                            Line 2, in test/integration/tests/q2.py 0
                            Failed example:
                                1 == 1
                            Expected:
                                False
                            Got:
                                True"""), 
                        "Did not pass correct tests"
                    )

    def test_notebook_class(self):
        """
        Checks that the otter.Notebook class works correctly
        """
        grader = Notebook("test/integration/tests")

        def square(x):
            return x**2

        def negate(x):
            return not x

        global_env = {
            "square" : square,
            "negate" : negate
        }

        for q_path in glob("test/integration/tests/*.py"):
            q = os.path.split(q_path)[1][:-3]
            result = grader.check(q, global_env=global_env)
            if q != "q2":
                self.assertEqual(result.grade, 1, "Test {} failed".format(q))
            else:
                self.assertEqual(result.grade, 0, "Test {} passed".format(q))
