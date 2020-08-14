################################
##### Tests for Otter Logs #####
################################

import unittest

from otter.argparser import get_parser

from . import TestCase

parser = get_parser()

TEST_FILES_PATH = "test/test-logs/"

class TestLogs(TestCase):

    def test_something(self):
        pass
