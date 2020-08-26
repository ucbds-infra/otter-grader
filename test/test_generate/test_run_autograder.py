####################################
##### Tests for otter generate #####
####################################
import os
import unittest
import subprocess
import json
import shutil

from subprocess import PIPE
from glob import glob
from unittest import mock
from shutil import copyfile

from otter.argparser import get_parser
from otter.generate.autograder import main as autograder
from otter.generate.run_autograder import main as run_autograder

from .. import TestCase

parser = get_parser()

TEST_FILES_PATH = "test/test_generate/test-run-autograder/"

class TestRunAutograder(TestCase):
    def setUp(self):
        super().setUp()

        self.env = {}
        with open(TEST_FILES_PATH + "run_autograder") as f:
            exec(f.read(), self.env)
        
        self.config = self.env["config"]

    def test_run_autograder(self):

        #generate the zip file 
        generate_command = ["generate", "autograder",
            "-t", TEST_FILES_PATH + "tests",
            "-o", TEST_FILES_PATH,
            "-r", TEST_FILES_PATH + "requirements.txt",
            TEST_FILES_PATH + "data/test-df.csv"
        ]
        args = parser.parse_args(generate_command)
        args.func = autograder
        args.func(args)

        # first unzip and check output
        os.mkdir(TEST_FILES_PATH + "autograder")
        unzip_command = ["unzip", "-o", TEST_FILES_PATH + "autograder.zip", "-d", TEST_FILES_PATH + "autograder/source"]
        unzip = subprocess.run(unzip_command, stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(unzip.stderr), 0, unzip.stderr.decode("utf-8"))

        self.config["autograder_dir"] = TEST_FILES_PATH + "autograder"

        # copy submission tests and notebook, 
        os.mkdir(TEST_FILES_PATH + "autograder/submission")
        os.mkdir(TEST_FILES_PATH + "autograder/results")
        copyfile(TEST_FILES_PATH + "fails2and6H.ipynb", TEST_FILES_PATH + "autograder/submission/fails2and6H.ipynb")

        run_autograder(self.config)

        self.assertDirsEqual(TEST_FILES_PATH + "autograder", TEST_FILES_PATH + "autograder-correct", ignore_ext=[".pdf",".zip"], ignore_dirs=["__pycache__"])

    def tearDown(self):
        for p in [TEST_FILES_PATH + "autograder", TEST_FILES_PATH + "autograder.zip", "test/results.json", TEST_FILES_PATH + "autograder-correct/__pycache__"]:
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.isfile(p):
                os.remove(p)
