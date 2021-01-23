"""
Abstract base classes for working with test files and classes to represent collections of test and 
their results
"""

from abc import ABC, abstractmethod
from collections import namedtuple
from textwrap import dedent
from typing import Tuple, List, Dict, Any
from jinja2 import Template
from pygments import highlight
from pygments.lexers import PythonConsoleLexer
from pygments.formatters import HtmlFormatter


# class for storing the test cases themselves
#   - body is the string that gets run for the test
#   - hidden is the visibility of the test case
TestCase = namedtuple("TestCase", ["name", "body", "hidden"])


# class for storing the results of a single test _case_ (within a test file)
#   - message should be a string to print out to the student (ignored if passed is True)
#   - passed is whether the test case passed
#   - hidden is the visibility of the test case
TestCaseResult = namedtuple("TestCaseResult", ["test_case", "message", "passed"])


# TODO: fix reprs
class TestFile(ABC):
    """
    A (abstract) single test file for Otter. This ABC defines how test results are represented and sets
    up the instance variables tracked by tests. Subclasses should implement the abstract class method
    ``from_file`` and the abstract instance method ``run``.

    Args:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list`` of ``TestCase``): a list of parsed tests to be run
        value (``float`` or ``list[float]``, optional): the point value of each test case, defaults to 1
        all_or_nothing (``bool``, optional): whether the test should be graded all-or-nothing across
            cases

    Attributes:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list`` of ``TestCase``): a list of parsed tests to be run
        values (``list[float]``): the point value of each test case, defaults to ``1/len(test_cases)``
        all_or_nothing (``bool``): whether the test should be graded all-or-nothing across
            cases
        passed_all (``bool``): whether all of the test cases were passed
        test_case_results (``list`` of ``TestCaseResult``): a list of results for the test cases in
            ``test_cases``
        grade (``float``): the percentage of ``points`` earned for this test file as a decimal
    """

    html_result_pass_template = Template("""
    <p><strong>{{ name }}</strong> passed!</p>
    """)

    plain_result_pass_template = Template("{{ name }} passed!")

    html_result_fail_template = Template("""
    <p><strong style='color: red;'>{{ name }}</strong></p>
    <p><strong>Test result:</strong></p>
    {% for test_case_result in test_case_results %}
        <p><em>{{ test_case_result.test_case.name }}</em>
        {% if not test_case_result.passed %}
            <pre>{{ test_case_result.message }}</pre>
        {% else %}
            <pre>Test case passed!</pre>
        {% endif %}
        </p>
    {% endfor %}
    """)

    plain_result_fail_template = Template(dedent("""\
    {{ name }} results:
    {% for test_case_result in test_case_results %}{% if not test_case_result.passed %}
    {{ test_case_result.message }}{% endif %}{% endfor %}"""))

    def _repr_html_(self):
        if self.passed_all:
            return type(self).html_result_pass_template.render(name=self.name)
        else:
            return type(self).html_result_fail_template.render(
                name=self.name,
                # test_code=highlight(self.failed_test, PythonConsoleLexer(), HtmlFormatter(noclasses=True)),
                test_case_results=self.test_case_results
            )

    def __repr__(self):
        if self.passed_all:
            return type(self).plain_result_pass_template.render(name=self.name)
        else:
            return type(self).plain_result_fail_template.render(
                name=self.name,
                # test_code=self.failed_test,
                test_case_results=self.test_case_results
            )

    # @abstractmethod
    def __init__(self, name, path, test_cases, value=1, all_or_nothing=True):
        self.name = name
        self.path = path
        # self.public_tests = [t for t, h in zip(tests, hiddens) if not h]
        # self.hidden_tests = [t for t, h in zip(tests, hiddens) if h]
        self.test_cases = test_cases
        if not isinstance(value, list):
            value = [value / len(self.test_cases) for _ in range(len(self.test_cases))]
        if len(value) != len(self.test_cases):
            raise ValueError(f"Length of 'value'{(len(value))} != length of 'test_caes' ({len(test_cases)})")
        self.values = value
        # self.hidden = hidden
        self.passed_all = None
        # self.failed_test = None
        # self.failed_test_hidden = None
        # self.result = None
        self.all_or_nothing = all_or_nothing
        self.test_case_results = []
        self.grade = None

    @classmethod
    @abstractmethod
    def from_file(cls, path):
        ...

    @abstractmethod
    def run(self, global_environment):
        ...
