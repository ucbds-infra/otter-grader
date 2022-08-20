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
        Checks a global environment against given test file. If ``global_env`` is ``None``, the global 
        environment of the calling frame is used; i.e., the following two calls are equivalent:

        .. code-block:: python

            check('tests/q1.py')
            check('tests/q1.py', global_env=globals())

        Args:
            nb_or_test_path (``str``): path to test file or notebook
            test_name (``str``, optional): the name of the test if a notebook metadata test
            global_env (``dict``, optional): a global environment resulting from the execution 
                of a python script or notebook

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
