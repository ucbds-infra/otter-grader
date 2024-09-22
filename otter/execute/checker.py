"""Class for running tests from test files"""

import inspect

from typing import Any, ClassVar, Optional

from ..nbmeta_config import NBMetadataConfig
from ..test_files import create_test_file, TestFile


class Checker:
    """
    A class for running and optionally tracking checks against test files.

    This class is not meant to be instantiated and is composed solely of class methods.
    """

    _track_results: ClassVar[bool] = False
    """whether to store check results"""

    _test_files: ClassVar[list[TestFile]] = []
    """stored check results"""

    def __new__(cls, *args: Any, **kwargs: Any):
        raise NotImplementedError("The Checker class cannot be instantiated")

    @classmethod
    def enable_tracking(cls):
        """
        Enable the tracking of test results from calls to ``check``.
        """
        cls._track_results = True

    @classmethod
    def disable_tracking(cls):
        """
        Disable the tracking of test results from calls to ``check``.
        """
        cls._track_results = False

    @classmethod
    def get_results(cls) -> list[TestFile]:
        """
        Get a pointer to the list into which check results are being collected.
        """
        return cls._test_files

    @classmethod
    def clear_results(cls):
        """
        Overwrite the pointer to the check result collection list.

        Does not affect the original list, only overwrites the field in the ``Checker`` class that
        points to it.
        """
        cls._test_files = []

    @classmethod
    def check(
        cls,
        nb_or_test_path: str,
        nbmeta_config: NBMetadataConfig,
        test_name: Optional[str] = None,
        global_env: Optional[dict[str, Any]] = None,
    ) -> TestFile:
        """
        Checks a global environment against a test, which may be stored in a file or in a notebook's
        metadata.

        Args:
            nb_or_test_path (``str``): path to test file or notebook
            test_name (``str``): the name of the test if a notebook metadata test
            global_env (``dict``): the global environment in which to run the test; if
                unspecified, the calling frame's global environment is used

        Returns:
            ``otter.test_files.abstract_test.TestFile``: result of running the tests in the
            given global environment
        """
        test = create_test_file(nb_or_test_path, nbmeta_config, test_name=test_name)

        if global_env is None:
            global_env = inspect.currentframe().f_back.f_globals

        test.run(global_env)

        if cls._track_results:
            cls._test_files.append(test)

        return test

    @classmethod
    def check_if_not_already_checked(
        cls, test_path: str, global_env: Optional[dict[str, Any]] = None
    ) -> Optional[TestFile]:
        """
        Run the specified test if it has not already been run (that is, if its result is not cached
        in this ``Checker`` instance).

        This method only works with test files.

        Args:
            test_path (``str``): path to test file
            global_env (``dict[str, Any] | None``): the global environment in which to run the test; if
                unspecified, the calling frame's global environment is used

        Returns:
            ``otter.test_files.abstract_test.TestFile | None``: result of running the tests in the
            given global environment
        """
        if any(test_path in tf.path or tf.path in test_path for tf in cls._test_files):
            return

        if global_env is None:
            global_env = inspect.currentframe().f_back.f_globals

        return cls.check(test_path, NBMetadataConfig(), global_env=global_env)
