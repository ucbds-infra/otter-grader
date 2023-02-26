"""Class for running tests from test files"""

import inspect

from ..test_files import create_test_file


class Checker:
    """
    A class for running and optionally tracking checks against test files.

    This class is not meant to be instantiated and is composed solely of class methods.
    """

    _track_results = False
    _test_files = []

    def __new__(cls, *args, **kwargs):
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
    def get_results(cls):
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
    def check(cls, nb_or_test_path, test_name=None, global_env=None):
        """
        Checks a global environment against a test, which may be stored in a file or in a notebook's
        metadata.

        Args:
            nb_or_test_path (``str``): path to test file or notebook
            test_name (``str``, optional): the name of the test if a notebook metadata test
            global_env (``dict``, optional): the global environment in which to run the test; if
                unspecified, the calling frame's global environment is used

        Returns:
            ``otter.test_files.abstract_test.TestFile``: result of running the tests in the 
            given global environment
        """
        test = create_test_file(nb_or_test_path, test_name=test_name)

        if global_env is None:
            global_env = inspect.currentframe().f_back.f_globals

        test.run(global_env)

        if cls._track_results:
            cls._test_files.append(test)

        return test

    @classmethod
    def check_if_not_already_checked(cls, test_path, global_env=None):
        """
        Run the specified test if it has not already been run (that is, if its result is not cached
        in this ``Checker`` instance).

        This method only works with test files.

        Args:
            test_path (``str``): path to test file
            global_env (``dict``, optional): the global environment in which to run the test; if
                unspecified, the calling frame's global environment is used

        Returns:
            ``otter.test_files.abstract_test.TestFile``: result of running the tests in the 
            given global environment
        """
        if any(test_path in tf.path or tf.path in test_path for tf in cls._test_files):
            return

        if global_env is None:
            global_env = inspect.currentframe().f_back.f_globals

        return cls.check(test_path, global_env=global_env)
