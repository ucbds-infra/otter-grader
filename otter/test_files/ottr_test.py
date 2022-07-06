"""A class to collect test file data from R autograding with Ottr"""

from .abstract_test import TestFile


class OttrTestFile(TestFile):

    def run(self, global_environment):
        raise NotImplementedError("Ottr test files cannot be run from Python")

    @classmethod
    def from_file(cls, path):
        raise NotImplementedError("Cannot create Ottr test files from a file in Python")
