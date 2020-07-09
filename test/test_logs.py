################################
##### Tests for Otter Logs #####
################################

import unittest

# read in argument parser
bin_globals = {}

with open("bin/otter") as f:
    exec(f.read(), bin_globals)

parser = bin_globals["parser"]

TEST_FILES_PATH = "test/test-logs/"

class TestLogs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n\n\n" + ("=" * 60) + f"\nRunning {__name__}.{cls.__name__}\n" + ("=" * 60) + "\n")
    
    def test_something(self):
        pass
