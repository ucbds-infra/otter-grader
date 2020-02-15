import os
import pandas as pd
import unittest
import subprocess
from subprocess import PIPE
from glob import glob
from otter import Notebook

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_image_cmd = ["make", "docker-test"]
        create_image = subprocess.run(create_image_cmd, stdout=PIPE, stderr=PIPE)
        # cls.assertEqual(len(create_image.stderr), 0, create_image.stderr.decode("utf-8"))

    def test_docker(self):
        """
        Check that we have the right container installed and that docker is running
        """
        # use docker image inspect to see that the image is installed and tagged as otter-grader
        inspect_command = ["docker", "image", "inspect", "otter-test"]
        inspect = subprocess.run(inspect_command, stdout=PIPE, stderr=PIPE)

        # assert that it didn't fail, it will fail if it is not installed
        self.assertEqual(len(inspect.stderr), 0, inspect.stderr)

    def test_hundred_notebooks(self):
        """
        Check that the example of 100 notebooks runs correctely locally.
        """
        # grade the 100 notebooks
        grade_command = ["python3", "-m", "otter.cli",
            "-y", "test/integration/manual-test/meta.yml", 
            "-p", "test/integration/manual-test/", 
            "-t", "test/integration/tests/", 
            "-r", "test/integration/requirements.txt",
            "-o", "test/",
            "--image", "otter-test"
        ]
        grade = subprocess.run(grade_command, stdout=PIPE, stderr=PIPE)

        # assert that otter-grader succesfully ran
        self.assertEqual(len(grade.stderr), 0, grade.stderr)

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
        grade_command = ["python3", "-m", "otter.cli",
            "-sy", "test/integration/py-tests/meta.yml", 
            "-p", "test/integration/py-tests/", 
            "-t", "test/integration/tests/", 
            "-r", "test/integration/requirements.txt",
            "-o", "test/",
            "--image", "otter-test"
        ]
        grade = subprocess.run(grade_command, stdout=PIPE, stderr=PIPE)

        # assert that otter-grader succesfully ran
        self.assertEqual(len(grade.stderr), 0, grade.stderr)

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

    def test_gs_generator(self):
        """
        Check that the correct zipfile is created by gs_generator.py
        """
        # create the zipfile
        gen_command = ["python3", "-m", "otter.gs_generator",
            "-t", "test/integration/tests",
            "-o", "test/",
            "-r", "test/integration/requirements.txt",
            "test/integration/test-df.csv"
        ]
        gen = subprocess.run(gen_command, stdout=PIPE, stderr=PIPE)

        # assert that otter-grader succesfully ran
        self.assertEqual(len(gen.stderr), 0, gen.stderr)

        # unzip the zipfile
        unzip_command = ["unzip", "-n", "test/autograder.zip", "-d", "test/autograder"]
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
        cleanup_command = ["rm", "-rf", "test/autograder", "test/autograder.zip"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)

        # assert cleanup worked
        self.assertEqual(len(cleanup.stderr), 0, "Error in cleanup")

    def test_script_checker(self):
        """
        Checks that the script checker works
        """
        # run for each individual test
        for file in glob("test/integration/tests/*.py"):
            check_command = ["python3", "-m", "otter.script", 
                "test/integration/py-tests/file0.py", 
                "-q", os.path.split(file)[1][:-3],
                "-t", os.path.split(file)[0]
            ]
            check = subprocess.run(check_command, stdout=PIPE, stderr=PIPE)

            # make sure there is no error
            self.assertEqual(len(check.stderr), 0, check.stderr)

            # make sure all tests except q2 pass
            if os.path.split(file)[1] != "q2.py":
                self.assertEqual(check.stdout.decode("utf-8"), "All tests passed!\n", check.stdout)

        # run checker command
        check_command = check_command = ["python3", "-m", "otter.script", 
                "test/integration/py-tests/file0.py", 
                "-t", "test/integration/tests"
            ]
        check = subprocess.run(check_command, stdout=PIPE, stderr=PIPE)

        # make sure there is no error
        self.assertEqual(len(check.stderr), 0, check.stderr)

        # make sure there is a failed test
        self.assertNotEqual(check.stdout.decode("utf-8"), "All tests passed!", check.stdout)

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
