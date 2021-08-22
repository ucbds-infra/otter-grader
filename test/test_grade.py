#################################
##### Tests for otter grade #####
#################################

import pandas as pd
import os
import re
import shutil
import subprocess
import unittest

from glob import glob
from subprocess import PIPE
from unittest import mock

from otter.generate import main as generate
from otter.grade import main as grade

from . import TestCase


TEST_FILES_PATH = "test/test-grade/"


class TestGrade(TestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        create_image_cmd = ["make", "docker-test"]
        subprocess.run(create_image_cmd, check=True)

        create_image_cmd = ["make", "docker-grade-test"]
        subprocess.run(create_image_cmd, check=True)

        shutil.copy("otter/grade/Dockerfile", "otter/grade/old-Dockerfile")
        with open("otter/grade/Dockerfile", "r+") as f:
            lines = f.readlines()

            idx = max([i if "ARG" in lines[i] else -1 for i in range(len(lines))])
            lines.insert(idx + 1, "ADD . /home/otter-grader\n")

            f.seek(0)
            f.write("".join(lines))
        
    def setUp(self):
        """
        Load in point values
        """
        self.test_points = {}
        for test_file in glob(TEST_FILES_PATH + "tests/*.py"):
            env = {}
            with open(test_file) as f:
                exec(f.read(), env)
            self.test_points[env['test']['name']] = env['test']['points']
        return super().setUp()

    @staticmethod
    def generate_autograder_zip(pdfs=False):
        generate(
            tests_path = TEST_FILES_PATH + "tests", 
            requirements = TEST_FILES_PATH + "requirements.txt", 
            output_dir = TEST_FILES_PATH,
            config = TEST_FILES_PATH + "otter_config.json" if pdfs else None,
            no_environment = True,
        )

    def test_docker(self):
        """
        Check that we have the right container installed and that docker is running
        """
        # use docker image inspect to see that the image is installed and tagged as otter-grader
        inspect = subprocess.run(["docker", "image", "inspect", "otter-test"], stdout=PIPE, stderr=PIPE)

        # assert that it didn't fail, it will fail if it is not installed
        self.assertEqual(len(inspect.stderr), 0, inspect.stderr.decode("utf-8"))

    def test_notebooks_with_pdfs(self):
        """
        Check that the example of 100 notebooks runs correctely locally.
        """
        self.generate_autograder_zip(pdfs=True)

        # grade the 100 notebooks
        grade(
            path = TEST_FILES_PATH + "notebooks/", 
            output_dir = "test/",
            autograder = TEST_FILES_PATH + "autograder.zip",
            containers = 5,
            image = "otter-test",
        )

        # read the output and expected output
        df_test = pd.read_csv("test/final_grades.csv")

        # sort by filename
        df_test = df_test.sort_values("file").reset_index(drop=True)
        df_test["failures"] = df_test["file"].apply(lambda x: [int(n) for n in re.split(r"\D+", x) if len(n) > 0])

        # add score sum cols for tests
        for test in self.test_points:
            test_cols = [l for l in df_test.columns if bool(re.search(fr"\b{test}\b", l))]
            df_test[test] = df_test[test_cols].sum(axis=1)

        # check point values
        for _, row in df_test.iterrows():
            for test in self.test_points:
                if int(re.sub(r"\D", "", test)) in row["failures"]:
                    # q6.py has all_or_nothing set to False, so if the hidden tests fail you should get 2.5 points
                    if "6H" in row["file"] and "q6" == test:
                        self.assertEqual(row[test], 2.5, "{} supposed to fail {} but passed".format(row["file"], test))
                    else:
                        self.assertEqual(row[test], 0, "{} supposed to fail {} but passed".format(row["file"], test))
                else:
                    self.assertEqual(row[test], self.test_points[test], "{} supposed to pass {} but failed".format(row["file"], test))

        # remove the extra output
        cleanup_command = ["rm", "-rf", "test/final_grades.csv", "test/submission_pdfs", "test/final_grades.csv", TEST_FILES_PATH + "autograder.zip"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(cleanup.stderr), 0, cleanup.stderr.decode("utf-8"))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        create_image_cmd = ["make", "cleanup-docker-grade-test"]
        subprocess.run(create_image_cmd, check=True)
        if os.path.exists("otter/grade/old-Dockerfile"):
            os.remove("otter/grade/Dockerfile")
            shutil.move("otter/grade/old-Dockerfile", "otter/grade/Dockerfile")
        
        # prune images
        grade(prune=True, force=True)
