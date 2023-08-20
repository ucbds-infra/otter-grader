"""Support for notebook metadata test files"""

import json

from .exception_test import ExceptionTestFile
from .ok_test import OKTestFile

from ..nbmeta_config import NBMetadataConfig
from ..utils import NOTEBOOK_METADATA_KEY


class _NotebookMetadataTestFileMixin:
    """
    """

    @classmethod
    def from_file(cls, path, test_name):
        """
        Parse an exception-based test from a Jupyter notebook's metadata and return an 
        ``ExceptionTestFile``.

        Args:
            path (``str``): the path to the notebook
            test_name (``str``): the name of the test to extract from the metadata

        Returns:
            ``ExceptionTestFile``: the new ``ExceptionTestFile`` object created from the given file
        """
        with open(path, encoding="utf-8") as f:
            nb = json.load(f)

        test_spec = nb["metadata"][NOTEBOOK_METADATA_KEY]["tests"]
        if test_name not in test_spec:
            raise ValueError(f"Test {test_name} not found")

        test_spec = test_spec[test_name]
        return cls.from_string(test_spec, path=path)

    @classmethod
    def from_nbmeta_config(cls, path: str, nbmeta_config: NBMetadataConfig, test_name: str):
        """
        """
        test_spec = nbmeta_config.tests
        if test_name not in test_spec:
            raise ValueError(f"Test {test_name} not found")

        test_spec = test_spec[test_name]
        return cls.from_string(test_spec, path=path)


class NotebookMetadataExceptionTestFile(ExceptionTestFile, _NotebookMetadataTestFileMixin):
    """
    A single notebook metadata test file for Otter.

    Tests are defined in the metadata of a jupyter notebook as a JSON object with the ``otter`` key.
    The tests themselves are assumed to be base-64-encoded compiled ``code`` objects from test files.

    .. code-block:: json

    {
        "metadata": {
            "otter": {
                "tests": {
                    "q1": ""
                }
            }
        }
    }
    """


class NotebookMetadataOKTestFile(OKTestFile, _NotebookMetadataTestFileMixin):
    """
    A single notebook metadata test file for Otter.

    Tests are defined in the metadata of a jupyter notebook as a JSON object with the ``otter`` key.
    The tests themselves are OK-formatted.

    .. code-block:: json

    {
        "metadata": {
            "otter": {
                "tests": {
                    "q1": {}
                }
            }
        }
    }
    """
