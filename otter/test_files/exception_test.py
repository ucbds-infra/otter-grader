"""Exception-based test files"""

import inspect
import pathlib

from dataclasses import replace
from functools import lru_cache
from textwrap import indent

from .abstract_test import TestCase, TestCaseResult, TestFile


class test_case:
    """
    A test case function decorator for Otter's exception-based test file format.

    Holds metadata for the test cases, as well as the test case function itself, and handles calling
    the function.

    Args:
        name (``str``, optional): the name of test case
        points (numeric, optional): the point value of the test case, if applicable
        hidden (``bool``, optional): whether the test case is hidden
        success_message (``str``, optional): a message to display to students if the test case passes
        failure_message (``str``, optional): a message to display to students if the test case fails

    Attributes:
        name (``str``): the name of test case
        points (numeric): the point value of the test case, if applicable
        hidden (``bool``): whether the test case is hidden
        success_message (``str``): a message to display to students if the test case passes
        failure_message (``str``): a message to display to students if the test case fails
        test_func (callable): the test case function being decorated
    """

    def __init__(self, name=None, points=None, hidden=False, success_message=None, failure_message=None):
        self.name = name
        self.points = points
        self.hidden = hidden
        self.success_message = success_message
        self.failure_message = failure_message
        self.test_func = None

    def __call__(self, test_func):
        """
        Wrap a test case function as a decorator.
        """
        self.test_func = test_func
        return self

    def to_dataclass(self):
        """
        Convert this test case to a ``TestCase`` named tuple for use in Otter's test file internals.

        Returns:
            ``otter.test_files.abstract_test.TestCase``: the test case named tuple
        """
        return TestCase(name=self.name, body=self, hidden=self.hidden, points=self.points, 
            success_message=self.success_message, failure_message=self.failure_message)

    def _get_func_params(self):
        """
        Get the list of parameters expected by the decorated test case function.

        Returns:
            ``list[str]``: the function argument names
        """
        return list(inspect.signature(self.test_func).parameters.keys())

    def call_func(self, global_environment):
        """
        Call the underlying test case function, passig in parameters from the global environment.

        If the signature of ``self.test_func`` contains a parameter called ``env``, the environment
        is passed in. For all other parameters, that value from the global environment is passed in, 
        defaulting to ``None`` if the key is not present. Thus, a function with the signature

        .. code-block:: python

            foo(env, func_a, func_b, obj)

        would get called as

        .. code-block:: python

            foo(
                env = global_environment, 
                func_a = global_environment.get("func_a"), 
                func_b = global_environment.get("func_b"),
                obj = global_environment.get("obj"),
            )

        Returns:
            ``object``: the return value of the test case function
        """
        args = self._get_func_params()
        call_kwargs = {arg: (global_environment if arg == "env" else \
                global_environment.get(arg, None)) for arg in args}
        return self.test_func(**call_kwargs)


class ExceptionTestFile(TestFile):
    """
    A single exception-based test file for Otter.

    Args:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list`` of ``TestCase``): a list of parsed tests to be run
        value (``int``, optional): the point value of this test, defaults to 1
        all_or_nothing (``bool``, optional): whether the test should be graded all-or-nothing across
            cases

    Attributes:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list`` of ``TestCase``): a list of parsed tests to be run
        value (``int``): the point value of this test, defaults to 1
        all_or_nothing (``bool``): whether the test should be graded all-or-nothing across
            cases
        passed_all (``bool``): whether all of the test cases were passed
        test_case_results (``list`` of ``TestCaseResult``): a list of results for the test cases in
            ``test_cases``
        grade (``float``): the percentage of ``points`` earned for this test file as a decimal
        source (``str``): the test file contents
    """

    source = None

    @property
    @lru_cache(1)
    def source_lines(self):
        """
        The lines of ``self.source``
        """
        return self.source.split("\n")

    def _generate_error_message(self, excp, context=0):
        """
        Generate an error message including the line that errored from ``self.source``.

        Args:
            excp (``Exception``): the exception to generate the message for
            context (``int``, optional): a number of extra lines of context to include from above
                and below the line that caused the exception

        Returns:
            ``str``: the error message
        """
        line_idx = excp.__traceback__.tb_next.tb_next.tb_lineno - 1
        l, h = max(0, line_idx - context), min(len(self.source_lines), line_idx + context + 1)
        lines = indent("\n".join(self.source_lines[l:h]), "  ")
        err_msg = str(excp).strip("'")
        return f"Error at line {line_idx + 1} in test {self.name}:\n{lines}\n{type(excp).__name__}: {err_msg}"

    def run(self, global_environment):
        """
        Run the test cases against ``global_environment``, saving the results in 
        ``self.test_case_results``.

        Arguments:
            ``global_environment`` (``dict``): result of executing a Python notebook/script
        """
        test_case_results = []
        for tc in self.test_cases:
            test_case = tc.body
            passed, message = True, "✅ Test case passed"
            try:
                test_case.call_func(global_environment)
            except Exception as e:
                passed, message = False, "❌ Test case failed\n" + self._generate_error_message(e)

            test_case_results.append(TestCaseResult(test_case=tc, message=message, passed=passed))

        self.test_case_results = test_case_results

    @staticmethod
    def _compile_string(s, path="<string>"):
        """
        Compile a string for execution.

        Args:
            s (``str``): the string to compile
            path (``str``, optional): the path to the test file

        Returns:
            ``code``: the compiled code of the file
        """
        return compile(s, path, "exec")

    @classmethod
    def _from_compiled_code(cls, code, path=""):
        """
        Parse a compiled exception-based test file and return an ``ExceptionTestFile``.

        Args:
            code (``code``): the compiled code of the test file
            path (``str``): the path to the test file

        Returns:
            ``ExceptionTestFile``: the new ``ExceptionTestFile`` object created from the given file
        """
        env = {}
        exec(code, env)

        if "name" not in env:
            raise ValueError(f"Test file {path} does not define 'name'")

        name = env["name"]
        points = env.get("points", None)
        test_cases = []
        for _, v in env.items():
            if isinstance(v, test_case):
                tc = v.to_dataclass()
                if tc.name is None:
                    tc = replace(tc, name=f"{name} - {len(test_cases) + 1}")
                test_cases.append(tc)

        test_cases = cls.resolve_test_file_points(points, test_cases)

        path = str(pathlib.Path(path).as_posix())
        return cls(name, path, test_cases, all_or_nothing=False)

    @classmethod
    def from_string(cls, s, path="<string>"):
        """
        Parse an exception-based test file as a string and return an ``ExceptionTestFile``.

        Args:
            s (``str``): the test file
            path (``str``, optional): the path to the test file

        Returns:
            ``ExceptionTestFile``: the new ``ExceptionTestFile`` object created from the given file
        """
        code = cls._compile_string(s, path=path)
        instc = cls._from_compiled_code(s, path=path)
        instc.source = s
        return instc

    @classmethod
    def from_file(cls, path):
        """
        Parse an exception-based test file and return an ``ExceptionTestFile``.

        Args:
            path (``str``): the path to the test file

        Returns:
            ``ExceptionTestFile``: the new ``ExceptionTestFile`` object created from the given file
        """
        with open(path) as f:
            source = f.read()
        return cls.from_string(source, path=path)
