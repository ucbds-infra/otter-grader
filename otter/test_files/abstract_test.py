"""
Abstract base classes for working with test files and classes to represent collections of test and 
their results
"""

from abc import ABC, abstractmethod
from textwrap import dedent
from typing import Tuple, List, Dict, Any
from jinja2 import Template
from pygments import highlight
from pygments.lexers import PythonConsoleLexer
from pygments.formatters import HtmlFormatter

class TestFile(ABC):
    html_result_pass_template = Template("""
    <p><strong>{{ name }}</strong> passed!</p>
    """)

    plain_result_pass_template = Template("{{ name }} passed!")

    html_result_fail_template = Template("""
    <p><strong style='color: red;'>{{ name }}</strong></p>
    <p><strong>Test code:</strong><pre>{{test_code}}</pre></p>
    <p><strong>Test result:</strong><pre>{{test_result}}</pre></p>
    """)

    plain_result_fail_template = Template(dedent("""\
       {{ name }}

    Test result:
    {{test_result}}"""))

    def _repr_html_(self):
        if self.passed:
            return type(self).html_result_pass_template.render(name=self.name)
        else:
            return type(self).html_result_fail_template.render(
                name=self.name,
                test_code=highlight(self.failed_test, PythonConsoleLexer(), HtmlFormatter(noclasses=True)),
                test_result=self.result
            )

    def __repr__(self):
        if self.passed:
            return type(self).plain_result_pass_template.render(name=self.name)
        else:
            return type(self).plain_result_fail_template.render(
                name=self.name,
                test_code=self.failed_test, # highlight(self.failed_test, PythonConsoleLexer(), HtmlFormatter(noclasses=True)),
                test_result=self.result
            )

    # @abstractmethod
    def __init__(self, name, tests, hiddens, value=1, hidden=True):
        self.name = name
        self.public_tests = [t for t, h in zip(tests, hiddens) if not h]
        self.hidden_tests = [t for t, h in zip(tests, hiddens) if h]
        self.value = value
        self.hidden = hidden
        self.passed = None
        self.failed_test = None
        self.failed_test_hidden = None
        self.result = None

    @classmethod
    @abstractmethod
    def from_file(cls, path):
        ...

    @abstractmethod
    def run(self, global_environment):
        ...
    
class TestCollection:
    def __init__(self, test_paths: List[str], test_class: TestFile):
        self.paths = test_paths
        self.tests = [test_class.from_file(path) for path in self.paths if "__init__.py" not in path]
    
    def run(self, global_environment, include_grade=True):
        """Run this object's tests on a given global environment (from running a notebook/script)
        
        Arguments:
            global_environment (``dict``): result of executing a Python notebook/script
            include_grade (``bool``, optional): whether grade should be included in result
        
        Returns:
            ``TestCollectionResults``: object resulting from running tests on ``global_environment`` 
                with grade, tests passed, and more information
        """
        passed_tests = []
        failed_tests = []
        grade = 0
        total = 0
        for t in self.tests:
            total += t.value
            passed, test_obj = t.run(global_environment)
            if passed:
                grade += t.value
                passed_tests.append(t)
            else:
                failed_tests.append((t, test_obj))

        try:
            grade /= total
        except ZeroDivisionError:
            grade = 0

        return TestCollectionResults(
            grade, self.paths, self.tests, passed_tests, failed_tests, include_grade
        )

class TestCollectionResults:
    html_result_template = Template("""
    {% if include_grade %}
    <strong>Grade: {{ grade }}</strong>
    {% endif %}
    {% if grade == 1.0 %}
        <p>All tests passed!</p>
    {% else %}
        <p>{{ passed_tests|length }} of {{ tests|length }} tests passed</p>
        {% if passed_tests %}
        <p> <strong>Tests passed:</strong>
            {% for passed_test in passed_tests %} {{ passed_test.name }} {% endfor %}
        </p>
        {% endif %}
        {% if failed_tests %}
        <p> <strong>Tests failed: </strong>
            <ul>
            {% for failed_test, failed_test_obj in failed_tests %}
                <li> {{ failed_test_obj._repr_html_() }} </li>
            {% endfor %}
            </ul>
        {% endif %}
    {% endif %}
    """)

    plain_result_template = Template("""{% if include_grade %}Grade: {{ grade }}{% endif %}
    {% if grade == 1.0 %}All tests passed!{% else %}
    {{ passed_tests|length }} of {{ tests|length }} tests passed
    {% if passed_tests %}
    Tests passed: {% for passed_test in passed_tests %} {{ passed_test.name }} {% endfor %}{% endif %}
    {% if failed_tests %}
    Tests failed:
    {% for failed_test, failed_test_obj in failed_tests %}
        {{ failed_test_obj.__repr__() }}
    {% endfor %}
    {% endif %}
    {% endif %}
    """)

    def __init__(self, grade, paths, tests, passed_tests, failed_tests, include_grade=True):
        self.grade = grade
        self.paths = paths
        self.tests = tests
        self.passed_tests = passed_tests
        self.failed_tests = failed_tests
        self.include_grade = include_grade

    def _repr_html_(self):
        return type(self).html_result_template.render(
            grade=self.grade,
            passed_tests=self.passed_tests,
            failed_tests=self.failed_tests,
            tests=self.tests,
            include_grade=self.include_grade
        )

    def _repr_gradescope_(self):
        return type(self).plain_result_template.render(
            grade=self.grade,
            passed_tests=self.passed_tests,
            failed_tests=self.failed_tests,
            tests=self.tests,
            include_grade=self.include_grade
        )

    def __repr__(self):
        return type(self).plain_result_template.render(
            grade=self.grade,
            passed_tests=self.passed_tests,
            failed_tests=self.failed_tests,
            tests=self.tests,
            include_grade=self.include_grade
        )

    
    
