#################################
##### Tests for otter grade #####
#################################

import os
import unittest
import subprocess
import shutil
import json
import re
import pandas as pd

from unittest import mock
from subprocess import PIPE
from glob import glob

# from otter.argparser import get_parser
from otter.grade import main as grade
from otter.grade.metadata import GradescopeParser, CanvasParser, JSONParser, YAMLParser
from otter.runner import run_otter

from . import TestCase

# parser = get_parser()

TEST_FILES_PATH = "test/test-grade/"

class TestGrade(TestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        create_image_cmd = ["make", "docker-test"]
        subprocess.run(create_image_cmd, check=True)
        # create_image = subprocess.run(create_image_cmd, check=True)
        # assert not create_image.stderr, create_image.stderr.decode("utf-8")

        create_image_cmd = ["make", "docker-grade-test"]
        subprocess.run(create_image_cmd, check=True)

        shutil.copy("otter/grade/Dockerfile", "otter/grade/old-Dockerfile")
        with open("otter/grade/Dockerfile", "r+") as f:
            lines = f.readlines()

            idx = max([i if "ARG" in lines[i] else -1 for i in range(len(lines))])
            lines.insert(idx + 1, "ADD . /home/otter-grader")

            f.seek(0)
            f.write("\n".join(lines))
        
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

    def generate_autograder_zip(self, pdfs=False):
        cmd = [
            "generate", "-t", TEST_FILES_PATH + "tests", "-r", 
            TEST_FILES_PATH + "requirements.txt", "-o", TEST_FILES_PATH
        ]
        if pdfs:
            cmd += ["-c", TEST_FILES_PATH + "otter_config.json"]
        run_otter(cmd)

    def test_docker(self):
        """
        Check that we have the right container installed and that docker is running
        """
        # use docker image inspect to see that the image is installed and tagged as otter-grader
        inspect = subprocess.run(["docker", "image", "inspect", "otter-test"], stdout=PIPE, stderr=PIPE)

        # assert that it didn't fail, it will fail if it is not installed
        self.assertEqual(len(inspect.stderr), 0, inspect.stderr.decode("utf-8"))

    def test_metadata_parsers(self):
        """
        Check that metadata parsers work correctly
        """
        correct_metadata = [
            {
                "identifier": "12345",
                "filename": "12345_empty_file.ipynb"
            }, {
                "identifier": "23456",
                "filename": "23456_empty_file.ipynb"
            }, {
                "identifier": "34567",
                "filename": "34567_empty_file.ipynb"
            }, {
                "identifier": "45678",
                "filename": "45678_empty_file.ipynb"
            }, {
                "identifier": "56789",
                "filename": "56789_empty_file.ipynb"
            }
        ]

        correct_file_to_id = {
            "12345_empty_file.ipynb": "12345",
            "23456_empty_file.ipynb": "23456",
            "34567_empty_file.ipynb": "34567",
            "45678_empty_file.ipynb": "45678",
            "56789_empty_file.ipynb": "56789",
        }

        correct_id_to_file = {
            "12345": "12345_empty_file.ipynb",
            "23456": "23456_empty_file.ipynb",
            "34567": "34567_empty_file.ipynb",
            "45678": "45678_empty_file.ipynb",
            "56789": "56789_empty_file.ipynb",
        }

        correct_filenames = [
            "12345_empty_file.ipynb",
            "23456_empty_file.ipynb",
            "34567_empty_file.ipynb",
            "45678_empty_file.ipynb",
            "56789_empty_file.ipynb",
        ]

        correct_identifiers = [
            "12345",
            "23456",
            "34567",
            "45678",
            "56789",
        ]

        try:
            # gradescope parser
            gs_parser = GradescopeParser(TEST_FILES_PATH + "gradescope-export")
            self.assertCountEqual(gs_parser.get_metadata(), correct_metadata)
            self.assertCountEqual(gs_parser.get_filenames(), correct_filenames)
            self.assertCountEqual(gs_parser.get_identifiers(), correct_identifiers)
            for file, identifier in zip(correct_file_to_id, correct_id_to_file):
                self.assertEqual(correct_file_to_id[file], gs_parser.file_to_id(file))
                self.assertEqual(correct_id_to_file[identifier], gs_parser.id_to_file(identifier))

            # canvas parser
            canvas_parser = CanvasParser(TEST_FILES_PATH + "canvas-export")
            self.assertCountEqual(canvas_parser.get_metadata(), correct_metadata)
            self.assertCountEqual(canvas_parser.get_filenames(), correct_filenames)
            self.assertCountEqual(canvas_parser.get_identifiers(), correct_identifiers)
            for file, identifier in zip(correct_file_to_id, correct_id_to_file):
                self.assertEqual(correct_file_to_id[file], canvas_parser.file_to_id(file))
                self.assertEqual(correct_id_to_file[identifier], canvas_parser.id_to_file(identifier))

            # JSON parser
            json_parser = JSONParser(TEST_FILES_PATH + "meta.json")
            self.assertCountEqual(json_parser.get_metadata(), correct_metadata)
            self.assertCountEqual(json_parser.get_filenames(), correct_filenames)
            self.assertCountEqual(json_parser.get_identifiers(), correct_identifiers)
            for file, identifier in zip(correct_file_to_id, correct_id_to_file):
                self.assertEqual(correct_file_to_id[file], json_parser.file_to_id(file))
                self.assertEqual(correct_id_to_file[identifier], json_parser.id_to_file(identifier))

            # YAML parser
            yaml_parser = YAMLParser(TEST_FILES_PATH + "meta.yml")
            self.assertCountEqual(yaml_parser.get_metadata(), correct_metadata)
            self.assertCountEqual(yaml_parser.get_filenames(), correct_filenames)
            self.assertCountEqual(yaml_parser.get_identifiers(), correct_identifiers)
            for file, identifier in zip(correct_file_to_id, correct_id_to_file):
                self.assertEqual(correct_file_to_id[file], yaml_parser.file_to_id(file))
                self.assertEqual(correct_id_to_file[identifier], yaml_parser.id_to_file(identifier))

            # cleanup
            gs_rm = subprocess.run(["rm", "-rf"] + glob(TEST_FILES_PATH + "gradescope-export/*.ipynb"), stdout=PIPE, stderr=PIPE)
            self.assertEqual(len(gs_rm.stderr), 0, gs_rm.stderr.decode("utf-8"))

        except:
            # cleanup
            gs_rm = subprocess.run(["rm", "-rf"] + glob(TEST_FILES_PATH + "gradescope-export/*.ipynb"), stdout=PIPE, stderr=PIPE)
            self.assertEqual(len(gs_rm.stderr), 0, gs_rm.stderr.decode("utf-8"))
            raise

    def test_notebooks_with_pdfs(self):
        """
        Check that the example of 100 notebooks runs correctely locally.
        """
        self.generate_autograder_zip(pdfs=True)

        # grade the 100 notebooks
        grade_command = ["grade",
            "-y", TEST_FILES_PATH + "notebooks/meta.yml", 
            "-p", TEST_FILES_PATH + "notebooks/", 
            # "-t", TEST_FILES_PATH + "tests/", 
            # "-r", TEST_FILES_PATH + "requirements.txt",
            "-o", "test/",
            # "--pdfs",
            "-a", TEST_FILES_PATH + "autograder.zip",
            "--containers", "5",
            "--image", "otter-test",
        ]
        # args = parser.parse_args(grade_command)
        # args.func = grade
        # args.func(args)
        run_otter(grade_command)

        # read the output and expected output
        df_test = pd.read_csv("test/final_grades.csv")

        # sort by filename
        df_test = df_test.sort_values("identifier").reset_index(drop=True)
        df_test["failures"] = df_test["identifier"].apply(lambda x: [int(n) for n in re.split(r"\D+", x) if len(n) > 0])

        # add score sum cols for tests
        for test in self.test_points:
            test_cols = [l for l in df_test.columns if bool(re.search(fr"\b{test}\b", l))]
            df_test[test] = df_test[test_cols].sum(axis=1)

        # check point values
        for _, row in df_test.iterrows():
            for test in self.test_points:
                if int(re.sub(r"\D", "", test)) in row["failures"]:
                    # q6.py has all_or_nothing set to False, so if the hidden tests fail you should get 2.5 points
                    if "6H" in row["identifier"] and "q6" == test:
                        self.assertEqual(row[test], 2.5, "{} supposed to fail {} but passed".format(row["identifier"], test))
                    else:
                        self.assertEqual(row[test], 0, "{} supposed to fail {} but passed".format(row["identifier"], test))
                else:
                    self.assertEqual(row[test], self.test_points[test], "{} supposed to pass {} but failed".format(row["identifier"], test))

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
        run_otter(["grade", "--prune", "-f"])
