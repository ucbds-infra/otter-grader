""""""

import inspect

from ..test_files import create_test_file


class Checker:
    """
    """

    _track_results = False
    _test_files = []

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("The Checker class cannot be instantiated")

    @classmethod
    def enable_tracking(cls):
        cls._track_results = True

    @classmethod
    def disable_tracking(cls):
        cls._track_results = False

    @classmethod
    def get_results(cls):
        return cls._test_files

    @classmethod
    def clear_results(cls):
        cls._test_files = []

    @classmethod
    def check(cls, nb_or_test_path, test_name=None, global_env=None):
        """
        Checks a global environment against given test file. If global_env is ``None``, the global 
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
