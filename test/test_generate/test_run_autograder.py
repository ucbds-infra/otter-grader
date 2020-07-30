####################################
##### Tests for otter generate #####
####################################

from otter.generate.run_autograder import main as run_autograder

from .. import TestCase

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test_generate/test-run-autograder/"

class TestRunAutograder(TestCase):

    def setUp(self):
        super().setUp()

        self.env = {}
        with open(TEST_FILES_PATH + "run_autograder") as f:
            exec(f.read(), self.env)
        
        self.config = self.env["config"]

    def test_run_autograder(self):
        # edit config
        
        run_autograder(self.config)

        # check output
    