###########################################
##### OK Test Parser for Otter-Grader #####
#####     forked from Gofer-Grader    #####
###########################################

import ast
import os
import doctest
import io
import string
import warnings

from glob import glob
from contextlib import redirect_stderr, redirect_stdout
from textwrap import dedent
from jinja2 import Template
from pygments import highlight
from pygments.lexers import PythonConsoleLexer
from pygments.formatters import HtmlFormatter

from .utils import hide_outputs


class CheckCallWrapper(ast.NodeTransformer):
    """Visits and replaces nodes in an abstract syntax tree in-place.
    
    Tracks import syntax and instances of ``otter.Notebook`` in an AST. Wraps calls to 
    ``otter.Notebook.check`` in calls to ``list.append`` to collect results of execution. Removes calls
    to ``otter.Notebook.check_all``, `otter.Notebook.export``, and ``otter.Notebook.to_pdf``.
    
    Args:
        secret (``str``): random digits string that prevents check function from being modified
    
    Attributes:
        secret (``str``): random digits string that prevents check function from being modified
    """
    OTTER_IMPORT_SYNTAX = "import"
    OTTER_IMPORT_NAME = "otter"
    OTTER_CLASS_NAME = "Notebook"
    OTTER_INSTANCE_NAME = "grader"

    def __init__(self, secret):
        self.secret = secret

    def check_node_constructor(self, expression):
        """Creates node that wraps expression in a list (``check_results_XX``) append call
        
        Args:
            expression (``ast.Name``): name for check function

        Returns:
            ``ast.Call``: function call object from calling check

        """
        args = [expression]
        func = ast.Attribute(
            attr='append',
            value=ast.Name(id='check_results_{}'.format(self.secret), ctx=ast.Load()),
            ctx=ast.Load(),
            keywords=[]
        )
        return ast.Call(func=func, args=args, keywords=[])

    def visit_ImportFrom(self, node):
        """
        Visits ``from ... import ...`` nodes and tracks the import syntax and alias of ``otter.Notebook``

        Args:
            node (``ast.ImportFrom``): the import node

        Returns:
            ``ast.ImportFrom``: the original node
        """
        if node.module == "otter" and "Notebook" in [n.name for n in node.names]:
            CheckCallWrapper.OTTER_IMPORT_SYNTAX = "from"
            nb_asname = [n.asname for n in node.names if n.name == "Notebook"][0]
            if nb_asname is not None:
                CheckCallWrapper.OTTER_CLASS_NAME = nb_asname
        return node

    def visit_Import(self, node):
        """
        Visits ``import ...`` nodes and tracks the import syntax and alias of ``otter``

        Args:
            node (``ast.Import``): the import node

        Returns:
            ``ast.Import``: the original node
        """
        if "otter" in [n.name for n in node.names]:
            CheckCallWrapper.OTTER_IMPORT_SYNTAX = "import"
            otter_asname = [n.asname for n in node.names if n.name == "otter"][0]
            if otter_asname is not None:
                CheckCallWrapper.OTTER_IMPORT_NAME = otter_asname
        return node

    def visit_Assign(self, node):
        """
        Visits assignment nodes to determine the name assigned to the instance of ``otter.Notebook``
        created.

        Args:
            node (``ast.Assign``): the assignment node

        Returns:
            ``ast.Assign``: the original node
        """
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Attribute) and CheckCallWrapper.OTTER_IMPORT_SYNTAX == "import":
                if node.value.func.attr == "Notebook" and isinstance(node.value.func.value, ast.Name):
                    if node.value.func.value.id == CheckCallWrapper.OTTER_IMPORT_NAME:
                        assert len(node.targets) == 1, "error parsing otter.Notebook instance in ast"
                        CheckCallWrapper.OTTER_INSTANCE_NAME = node.targets[0].id
            elif isinstance(node.value.func, ast.Name) and CheckCallWrapper.OTTER_IMPORT_SYNTAX == "from":
                if node.value.func.id == CheckCallWrapper.OTTER_CLASS_NAME:
                    assert len(node.targets) == 1, "error parsing otter.Notebook instance in ast"
                    CheckCallWrapper.OTTER_INSTANCE_NAME = node.targets[0].id
        return node

    def visit_Expr(self, node):
        """
        Visits expression nodes and removes them if they are calls to ``otter.Notebook.check_all``,
        ``otter.Notebook.export``, or ``otter.Notebook.to_pdf`` or wraps them using 
        ``CheckCallWrapper.check_node_constructor`` if they are calls to ``otter.Notebook.check``.

        Args:
            node (``ast.Expr``): the expression node

        Returns:
            ``ast.Expr``: the transformed node
            ``None``: if the node was a removed call
        """
        if isinstance(node.value, ast.Call):
            call_node = node.value
            if isinstance(call_node.func, ast.Attribute):
                if isinstance(call_node.func.value, ast.Name) and call_node.func.value.id == CheckCallWrapper.OTTER_INSTANCE_NAME:
                    if call_node.func.attr in ["check_all", "export", "to_pdf"]:
                        return None
                    elif call_node.func.attr == "check":
                        node.value = self.check_node_constructor(call_node)
        return node


def run_doctest(name, doctest_string, global_environment):
    """
    Run a single test with given ``global_environment``. Returns ``(True, '')`` if the doctest passes. 
    Returns ``(False, failure_message)`` if the doctest fails.

    Args:
        name (``str``): name of doctest
        doctest_string (``str``): doctest in string form
        global_environment (``dict``): global environment resulting from the execution of a python 
            script/notebook
    
    Returns:
        ``tuple`` of (``bool``, ``str``): results from running the test
    """
    examples = doctest.DocTestParser().parse(
        doctest_string,
        name
    )
    test = doctest.DocTest(
        [e for e in examples if isinstance(e, doctest.Example)],
        global_environment,
        name,
        None,
        None,
        doctest_string
    )

    doctestrunner = doctest.DocTestRunner(verbose=True)

    runresults = io.StringIO()
    with redirect_stdout(runresults), redirect_stderr(runresults), hide_outputs():
        doctestrunner.run(test, clear_globs=False)
    with open(os.devnull, 'w') as f, redirect_stderr(f), redirect_stdout(f):
        result = doctestrunner.summarize(verbose=True)
    # An individual test can only pass or fail
    if result.failed == 0:
        return (True, '')
    else:
        return False, runresults.getvalue()


class OKTest:
    """
    A single test (set of doctests) for Otter.
    
    Instances of this class are callable. When called, it takes a ``global_environment`` dict, and returns 
    an ``otter.ok_parser.OKTestsResult`` object. We only take a global_environment, *not* a 
    ``local_environment``. This makes tests not useful inside functions, methods or other scopes with 
    local variables. This is a limitation of doctest, so we roll with it.

    The last 2 attributes (``passed``, ``failed_test``) are set after calling ``run()``.

    Args:
        name (``str``): name of test
        tests (``list`` of ``str``): ;ist of docstring tests to be run
        hiddens (``list`` of ``bool``): visibility of each tests in ``tests``
        value (``int``, optional): point value of this test, defaults to 1
        hidden (``bool``, optional): wheter this test is hidden
    """
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
            return OKTest.html_result_pass_template.render(name=self.name)
        else:
            return OKTest.html_result_fail_template.render(
                name=self.name,
                test_code=highlight(self.failed_test, PythonConsoleLexer(), HtmlFormatter(noclasses=True)),
                test_result=self.result
            )

    def __repr__(self):
        if self.passed:
            return OKTest.plain_result_pass_template.render(name=self.name)
        else:
            return OKTest.plain_result_fail_template.render(
                name=self.name,
                test_code=self.failed_test, # highlight(self.failed_test, PythonConsoleLexer(), HtmlFormatter(noclasses=True)),
                test_result=self.result
            )

    def __init__(self, name, tests, hiddens, value=1, hidden=True):
        self.name = name
        self.public_tests = [t for t, h in zip(tests, hiddens) if not h]
        self.hidden_tests = [t for t, h in zip(tests, hiddens) if h]
        self.value = value
        self.hidden = hidden
        self.passed = None
        self.failed_test = None
        self.failed_test_hidden = None

    def run(self, global_environment):
        """Runs tests on a given ``global_environment``
        
        Arguments:
            ``global_environment`` (``dict``): result of executing a Python notebook/script
        
        Returns:
            ``tuple`` of (``bool``, ``otter.ok_parser.OKTest``): whether the test passed and a pointer 
                to the current ``otter.ok_parser.OKTest`` object
        """
        for i, t in enumerate(self.public_tests + self.hidden_tests):
            passed, result = run_doctest(self.name + ' ' + str(i), t, global_environment)
            if not passed:
                self.passed = False
                self.failed_test = t
                self.failed_test_hidden = i >= len(self.public_tests)
                self.result = result
                return False, self
        self.passed = True
        return True, self

    @classmethod
    def from_file(cls, path):
        """
        Parse an ok test file & return an ``OKTest``

        Args:
            path (``str``): path to ok test file

        Returns:
            ``otter.ok_parser.OKTest``: new ``OKTest`` object created from the given file
        """
        # ok test files are python files, with a global 'test' defined
        test_globals = {}
        with open(path) as f:
            exec(f.read(), test_globals)

        test_spec = test_globals['test']

        # We only support a subset of these tests, so let's validate!

        # Make sure there is a name
        assert 'name' in test_spec

        # Do not support multiple suites in the same file
        assert len(test_spec['suites']) == 1

        test_suite = test_spec['suites'][0]

        # Only support doctest. I am unsure if other tests are implemented
        assert test_suite.get('type', 'doctest') == 'doctest'

        # Not setup and teardown supported
        assert not bool(test_suite.get('setup'))
        assert not bool(test_suite.get('teardown'))

        if 'hidden' in test_spec:
            warnings.warn(
                "The global 'hidden' key of ok-tests is deprecated since v1.0.0. "
                "This key will be ignored.", 
                FutureWarning
            )

        tests = []
        hiddens = []

        for _, test_case in enumerate(test_spec['suites'][0]['cases']):
            tests.append(dedent(test_case['code']))
            hiddens.append(test_case.get('hidden', True))

        return cls(path, tests, hiddens, test_spec.get('points', 1), test_spec.get('hidden', True))


class OKTests:
    """Test class for ok-style tests used to grade assignments
    
    Args:
        test_paths (``list`` of ``str``): list of paths to ok tests
    """
    def __init__(self, test_paths):
        self.paths = test_paths
        self.tests = [OKTest.from_file(path) for path in self.paths if "__init__.py" not in path]

    def run(self, global_environment, include_grade=True):
        """Run this object's tests on a given global environment (from running a notebook/script)
        
        Arguments:
            global_environment (``dict``): result of executing a Python notebook/script
            include_grade (``bool``, optional): whether grade should be included in result
        
        Returns:
            ``otter.ok_parser.OKTestsResult``: object resulting from running tests on ``global_environment`` 
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

        return OKTestsResult(grade, self.paths, self.tests, passed_tests,
                             failed_tests, include_grade)


class OKTestsResult:
    """
    Displayable result generated from ``otter.ok_parser.OKTests``

    Args:
        grade (``float``): grade as a decimal in the range [0, 1]
        paths (``list`` of ``str``): list of paths to ok tests
        tests (``list`` of ``OKTest``): list of OKTest objects for each path
        passed_tests (``list`` of ``str``): list of passed test docstrings
        failed_tests (``list`` of ``str``, ``otter.ok_parser.OKTest``): list of failed test docstrings and
            ``OKTest`` objects
        include_grade (``bool``, optional): whether grade should be included in result

    Attributes:
        grade (``float``): grade as a decimal in the range [0, 1]
        paths (``list`` of ``str``): list of paths to ok tests
        tests (``list`` of ``OKTest``): list of OKTest objects for each path
        passed_tests (``list`` of ``str``): list of passed test docstrings
        failed_tests (``list`` of ``str``, ``otter.ok_parser.OKTest``): list of failed test docstrings and
            ``OKTest`` objects
        include_grade (``bool``, optional): whether grade should be included in result

    """

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
        return OKTestsResult.html_result_template.render(
            grade=self.grade,
            passed_tests=self.passed_tests,
            failed_tests=self.failed_tests,
            tests=self.tests,
            include_grade=self.include_grade
        )

    def _repr_gradescope_(self):
        return OKTestsResult.plain_result_template.render(
            grade=self.grade,
            passed_tests=self.passed_tests,
            failed_tests=self.failed_tests,
            tests=self.tests,
            include_grade=self.include_grade
        )

    def __repr__(self):
        return OKTestsResult.plain_result_template.render(
            grade=self.grade,
            passed_tests=self.passed_tests,
            failed_tests=self.failed_tests,
            tests=self.tests,
            include_grade=self.include_grade
        )
