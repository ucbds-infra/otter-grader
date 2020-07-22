################################
##### Tests for Otter Logs #####
################################

import unittest

from . import TestCase

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test-logs/"

class TestLogs(TestCase):

    def test_something(self):
        pass
