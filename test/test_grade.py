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

TEST_FILES_PATH = "test/test-grade/"

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
            "-y", TEST_FILES_PATH + "notebooks/meta.yml", 
            "-p", TEST_FILES_PATH + "notebooks/", 
            "-t", TEST_FILES_PATH + "tests/", 
            "-r", TEST_FILES_PATH + "requirements.txt",
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
        df_correct = pd.read_csv(TEST_FILES_PATH + "final_grades_correct_notebooks.csv").sort_values("identifier").reset_index(drop=True)

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
            "-sy", TEST_FILES_PATH + "scripts/meta.yml", 
            "-p", TEST_FILES_PATH + "scripts/", 
            "-t", TEST_FILES_PATH + "tests/", 
            "-r", TEST_FILES_PATH + "requirements.txt",
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
        df_correct = pd.read_csv(TEST_FILES_PATH + "final_grades_correct_script.csv").sort_values("identifier").reset_index(drop=True)

        # assert the dataframes are as expected
        self.assertTrue(df_test.equals(df_correct), "Dataframes not equal")

        # remove the extra output
        cleanup_command = ["rm", "test/final_grades.csv"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)

        # assert cleanup worked
        self.assertEqual(len(cleanup.stderr), 0, "Error in cleanup")
