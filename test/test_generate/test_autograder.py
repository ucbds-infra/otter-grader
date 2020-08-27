####################################
##### Tests for otter generate #####
####################################

import os
import unittest
import subprocess
import json

from subprocess import PIPE
from glob import glob
from unittest import mock

from otter.argparser import get_parser
from otter.generate.autograder import main as autograder

from .. import TestCase

parser = get_parser()

TEST_FILES_PATH = "test/test_generate/test-autograder/"

class TestAutograder(TestCase):

    def create_docker_image(self):
        create_image_cmd = ["make", "docker-test"]
        subprocess.run(create_image_cmd, check=True)
        # create_image = subprocess.run(create_image_cmd, check=True)
        # assert not create_image.stderr, create_image.stderr.decode("utf-8")

    def test_gs_generator(self):
        """
        Check that the correct zipfile is created by gs_generator.py
        """
        # create the zipfile
        generate_command = ["generate", "autograder",
            "-t", TEST_FILES_PATH + "tests",
            "-o", TEST_FILES_PATH,
            "-r", TEST_FILES_PATH + "requirements.txt",
            TEST_FILES_PATH + "data/test-df.csv"
        ]
        args = parser.parse_args(generate_command)
        args.func = autograder
        args.func(args)

        with self.unzip_to_temp(TEST_FILES_PATH + "autograder.zip", delete=True) as unzipped_dir:
            self.assertDirsEqual(unzipped_dir, TEST_FILES_PATH + "autograder-correct")

    def test_gradescope(self):
        """
        Checks that the Gradescope autograder works
        """
        self.create_docker_image()

        # generate the zipfile
        generate_command = ["generate", "autograder",
            "-t", TEST_FILES_PATH + "tests",
            "-o", TEST_FILES_PATH,
            "-r", TEST_FILES_PATH + "requirements.txt",
            TEST_FILES_PATH + "data/test-df.csv"
        ]
        args = parser.parse_args(generate_command)
        args.func = autograder
        args.func(args)

        # build the docker image
        subprocess.run(["docker", "build", TEST_FILES_PATH, "-t", "otter-gradescope-test"], check=True)
        # self.assertEqual(len(build.stderr), 0, build.stderr.decode("utf-8"))

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
        with open(TEST_FILES_PATH + "results-correct.json") as f:
            correct_results = json.load(f)
        with open("test/results.json") as f:
            results = json.load(f)
        self.assertEqual(results, correct_results, "Incorrect results when grading in Gradescope container")

        # cleanup files and container
        cleanup = subprocess.run(["rm", "-rf", TEST_FILES_PATH + "autograder", TEST_FILES_PATH + "autograder.zip", "test/results.json"], stdout=PIPE, stderr=PIPE)
        remove_container = subprocess.run(["docker", "rm", container_id], stdout=PIPE, stderr=PIPE)
        self.assertEqual(len(cleanup.stderr), 0, cleanup.stderr.decode("utf-8"))
        self.assertEqual(len(remove_container.stderr), 0, remove_container.stderr.decode("utf-8"))
