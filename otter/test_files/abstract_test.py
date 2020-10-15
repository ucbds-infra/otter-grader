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
        self.value = value
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

    
# class TestCollection:
#     def __init__(self, test_paths: List[str], test_class: TestFile):
#         self.paths = test_paths
#         self.test_files = [test_class.from_file(path) for path in self.paths if "__init__.py" not in path]
    
#     def run(self, global_environment, include_grade=True):
#         """Run this object's tests on a given global environment (from running a notebook/script)
        
#         Arguments:
#             global_environment (``dict``): result of executing a Python notebook/script
#             include_grade (``bool``, optional): whether grade should be included in result
        
#         Returns:
#             ``TestCollectionResults``: object resulting from running tests on ``global_environment`` 
#                 with grade, tests passed, and more information
#         """
#         test_case_results = []
#         score = 0
#         total = 0
#         for tf in self.test_files:
#             total += tf.value
#             tf.run(global_environment)
#             score += tf.value * tf.grade
#             test_case_results.extend(tf.test_case_results)
#             # if tf.passed:
#             #     passed_tests.append(tf)
#             # else:
#             #     failed_tests.append((t, test_obj))

#         try:
#             grade = score / total
#         except ZeroDivisionError:
#             grade = 0

#         return TestCollectionResults(
#             grade, self.paths, self.tests, test_case_results, include_grade
#         )

# class TestCollectionResults:
#     html_result_template = Template("""
#     {% if include_grade %}
#     <strong>Grade: {{ grade }}</strong>
#     {% endif %}
#     {% if grade == 1.0 %}
#         <p>All tests passed!</p>
#     {% else %}
#         <p>{{ passed_tests|length }} of {{ tests|length }} tests passed</p>
#         {% if passed_tests %}
#         <p> <strong>Tests passed:</strong>
#             {% for passed_test in passed_tests %} {{ passed_test.name }} {% endfor %}
#         </p>
#         {% endif %}
#         {% if failed_tests %}
#         <p> <strong>Tests failed: </strong>
#             <ul>
#             {% for failed_test, failed_test_obj in failed_tests %}
#                 <li> {{ failed_test_obj._repr_html_() }} </li>
#             {% endfor %}
#             </ul>
#         {% endif %}
#     {% endif %}
#     """)

#     plain_result_template = Template("""{% if include_grade %}Grade: {{ grade }}{% endif %}
#     {% if grade == 1.0 %}All tests passed!{% else %}
#     {{ passed_tests|length }} of {{ tests|length }} tests passed
#     {% if passed_tests %}
#     Tests passed: {% for passed_test in passed_tests %} {{ passed_test.name }} {% endfor %}{% endif %}
#     {% if failed_tests %}
#     Tests failed:
#     {% for failed_test, failed_test_obj in failed_tests %}
#         {{ failed_test_obj.__repr__() }}
#     {% endfor %}
#     {% endif %}
#     {% endif %}
#     """)

#     def __init__(self, grade, paths, tests, passed_tests, failed_tests, include_grade=True):
#         self.grade = grade
#         self.paths = paths
#         self.tests = tests
#         self.passed_tests = passed_tests
#         self.failed_tests = failed_tests
#         self.include_grade = include_grade

#     def _repr_html_(self):
#         return type(self).html_result_template.render(
#             grade=self.grade,
#             passed_tests=self.passed_tests,
#             failed_tests=self.failed_tests,
#             tests=self.tests,
#             include_grade=self.include_grade
#         )

#     def _repr_gradescope_(self):
#         return type(self).plain_result_template.render(
#             grade=self.grade,
#             passed_tests=self.passed_tests,
#             failed_tests=self.failed_tests,
#             tests=self.tests,
#             include_grade=self.include_grade
#         )

#     def __repr__(self):
#         return type(self).plain_result_template.render(
#             grade=self.grade,
#             passed_tests=self.passed_tests,
#             failed_tests=self.failed_tests,
#             tests=self.tests,
#             include_grade=self.include_grade
#         )
