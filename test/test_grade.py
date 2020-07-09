#################################
##### Tests for otter grade #####
#################################

import os
import unittest
import subprocess
import json
import re
import pandas as pd

from unittest import mock
from subprocess import PIPE
from glob import glob

from otter.grade import main as grade
from otter.metadata import GradescopeParser, CanvasParser, JSONParser, YAMLParser

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test-grade/"

class TestGrade(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("\n\n\n" + ("=" * 60) + f"\nRunning {__name__}.{cls.__name__}\n" + ("=" * 60) + "\n")

        create_image_cmd = ["make", "docker-test"]
        create_image = subprocess.run(create_image_cmd, stdout=PIPE, stderr=PIPE)
        assert not create_image.stderr, create_image.stderr.decode("utf-8")
    
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


    def test_notebooks(self):
        """
        Check that the example of 100 notebooks runs correctely locally.
        """
        # grade the 100 notebooks
        grade_command = ["grade",
            # NO METADATA PASSED, test case when no metadata provided
            # "-y", TEST_FILES_PATH + "notebooks/meta.yml", 
            "-p", TEST_FILES_PATH + "notebooks/", 
            "-t", TEST_FILES_PATH + "tests/", 
            "-r", TEST_FILES_PATH + "requirements.txt",
            "-o", "test/",
            "--image", "otter-test",
            "-v"
        ]
        args = parser.parse_args(grade_command)
        args.func = grade
        args.func(args)

        # read the output and expected output
        df_test = pd.read_csv("test/final_grades.csv")
        self.assertTrue("identifier" not in df_test.columns, "did not drop identifier column when no metadata passed")

        # sort by filename
        df_test = df_test.sort_values("file").reset_index(drop=True)
        df_test["failures"] = df_test["file"].apply(lambda x: [int(n) for n in re.split(r"\D+", x) if len(n) > 0])

        # check point values
        for _, row in df_test.iterrows():
            for test in self.test_points:
                if int(re.sub(r"\D", "", test)) in row["failures"]:
                    self.assertEqual(row[test], 0, "{} supposed to fail {} but passed".format(row["file"], test))
                else:
                    self.assertEqual(row[test], self.test_points[test], "{} supposed to pass {} but failed".format(row["file"], test))

        # df_correct = pd.read_csv(TEST_FILES_PATH + "final_grades_correct_notebooks.csv").sort_values("identifier").reset_index(drop=True)

        # # assert the dataframes are as expected
        # self.assertTrue(df_test.equals(df_correct), "Dataframes not equal")

        # remove the extra output
        cleanup_command = ["rm", "test/final_grades.csv"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)

        # assert cleanup worked
        self.assertEqual(len(cleanup.stderr), 0, "Error in cleanup")


    def test_notebooks_with_pdfs(self):
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
            "--pdfs", "tags",
            "--containers", "5",
            "--image", "otter-test"
        ]
        args = parser.parse_args(grade_command)
        args.func = grade
        args.func(args)

        # check that we have PDFs
        self.assertTrue(os.path.isdir("test/submission_pdfs"))
        for file in glob(TEST_FILES_PATH + "notebooks/*.ipynb"):
            pdf = "test/submission_pdfs/" + os.path.split(file)[1][:-5] + "pdf"
            self.assertTrue(os.path.isfile(pdf))

        # remove the extra output
        cleanup_command = ["rm", "-rf", "test/final_grades.csv", "test/submission_pdfs"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(cleanup.stderr), 0, cleanup.stderr.decode("utf-8"))


    def test_scripts(self):
        """
        Check that the example of 100 scripts runs correctely locally.
        """
        grade_command = ["grade",
            "-sy", TEST_FILES_PATH + "scripts/meta.yml", 
            "-p", TEST_FILES_PATH + "scripts/", 
            "-t", TEST_FILES_PATH + "tests/", 
            "-r", TEST_FILES_PATH + "requirements.txt",
            "-o", "test/",
            "--image", "otter-test"
        ]
        args = parser.parse_args(grade_command)
        args.func = grade
        args.func(args)

        # read the output and expected output
        df_test = pd.read_csv("test/final_grades.csv").sort_values("identifier").reset_index(drop=True)
        df_test["failures"] = df_test["identifier"].apply(lambda x: [int(n) for n in re.split(r"\D+", x) if len(n) > 0])

        # check point values
        for _, row in df_test.iterrows():
            for test in self.test_points:
                if int(re.sub(r"\D", "", test)) in row["failures"]:
                    self.assertEqual(row[test], 0, "{} supposed to fail {} but passed".format(row["identifier"], test))
                else:
                    self.assertEqual(row[test], self.test_points[test], "{} supposed to pass {} but failed".format(row["identifier"], test))
        
        # grade the 100 scripts
        
        # args = parser.parse_args(grade_command)
        # args.func = grade
        # args.func(args)

        # # read the output and expected output
        # df_test = pd.read_csv("test/final_grades.csv").sort_values("identifier").reset_index(drop=True)
        # df_correct = pd.read_csv(TEST_FILES_PATH + "final_grades_correct_script.csv").sort_values("identifier").reset_index(drop=True)

        # # assert the dataframes are as expected
        # self.assertTrue(df_test.equals(df_correct), "Dataframes not equal")

        # remove the extra output
        cleanup_command = ["rm", "test/final_grades.csv"]
        cleanup = subprocess.run(cleanup_command, stdout=PIPE, stderr=PIPE)

        # assert cleanup worked
        self.assertEqual(len(cleanup.stderr), 0, "Error in cleanup")
