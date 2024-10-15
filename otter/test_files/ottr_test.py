"""A class to collect test file data from R autograding with Ottr"""

from typing import Any

from .abstract_test import TestFile


class OttrTestFile(TestFile):

    def run(self, global_environment: dict[str, Any]):
        raise NotImplementedError("Ottr test files cannot be run from Python")

    @classmethod
    def from_file(cls, path: str) -> "OttrTestFile":
        raise NotImplementedError("Cannot create Ottr test files from a file in Python")

    @classmethod
    def from_metadata(cls, s: Any, path: str) -> "TestFile":
        raise NotImplementedError("Cannot create Ottr test files from a file in Python")
