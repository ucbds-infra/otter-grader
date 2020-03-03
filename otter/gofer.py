#######################################
##### Functions from Gofer-Grader #####
#######################################

from contextlib import redirect_stderr, redirect_stdout, contextmanager
import inspect
import ast
import os
import sys
from IPython import get_ipython

import doctest
import io
import itertools
import json
from glob import glob
import random
import string
from jinja2 import Template
from textwrap import dedent

from pygments import highlight
from pygments.lexers import PythonConsoleLexer
from pygments.formatters import HtmlFormatter

def flush_inline_matplotlib_plots():
    """
    Flush matplotlib plots immediately, rather than asynchronously.
    Basically, the inline backend only shows the plot after the entire
    cell executes, which means we can't easily use a contextmanager to
    suppress displaying it. See https://github.com/jupyter-widgets/ipywidgets/issues/1181/
    and https://github.com/ipython/ipython/issues/10376 for more details. This
    function displays flushes any pending matplotlib plots if we are using
    the inline backend.
    Stolen from https://github.com/jupyter-widgets/ipywidgets/blob/4cc15e66d5e9e69dac8fc20d1eb1d7db825d7aa2/ipywidgets/widgets/interaction.py#L35
    """
    if 'matplotlib' not in sys.modules:
        # matplotlib hasn't been imported, nothing to do.
        return

    try:
        import matplotlib as mpl
        from ipykernel.pylab.backend_inline import flush_figures
    except ImportError:
        return
    # except KeyError:
    #     return

    if mpl.get_backend() == 'module://ipykernel.pylab.backend_inline':
        flush_figures()

@contextmanager
def hide_outputs():
    """
    Context manager for hiding outputs from display() calls.
    IPython handles matplotlib outputs specially, so those are supressed too.
    """
    ipy = get_ipython()
    if ipy is None:
        # Not running inside ipython!
        yield
        return
    old_formatters = ipy.display_formatter.formatters
    ipy.display_formatter.formatters = {}
    try:
        yield
    finally:
        # flush_inline_matplotlib_plots()
        ipy.display_formatter.formatters = old_formatters

class CheckCallWrapper(ast.NodeTransformer):
    """NodeTransformer visits and replaces nodes in place.
    CheckCallWrapper finds nodes with check(..) and replaces it with
    check_results_<secret>(check(...))
    
    Args:
        secret (str): Random digits string that prevents check function from being modified
    
    Attributes:
        secret (str): Random digits string that prevents check function from being modified

    """

    def __init__(self, secret):
        self.secret = secret

    def node_constructor(self, expression):
        """Creates node that wraps expression in a list (check_results_XX) append call
        
        Args:
            expression (ast.Name): Name for check function

        Returns:
            ast.Call: Function call object from calling check

        """
        args = [expression]
        func = ast.Attribute(attr='append',
                             value=ast.Name(id='check_results_{}'.format(self.secret),
                                            ctx=ast.Load()),
                             ctx=ast.Load(),
                             keywords=[])
        return ast.Call(func=func, args=args, keywords=[])

    def visit_Call(self, node):
        """Function that handles whether a given function call is a 'check' call
        and transforms the node accordingly.
        
        Args:
            node (ast.Call): Function call object, calling the check function

        Returns:
            ast.Call: Transformed version of input node

        """
        # test case is if check is .check
        if isinstance(node.func, ast.Attribute):
            return node
        elif isinstance(node.func, ast.Name):
            if node.func.id == 'check':
                return self.node_constructor(node)
            else:
                return node
        else:
            return node

def run_doctest(name, doctest_string, global_environment):
    """
    Run a single test with given global_environment.
    Returns (True, '') if the doctest passes.
    Returns (False, failure_message) if the doctest fails.

    Args:
        name (str): Name of doctest
        doctest_string (str): Doctest in string form
        global_environment (dict of str: str): Global environment resulting from the execution
            of a python script/notebook
    
    Returns:
        (bool, str): Results from running the test

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
    A single DocTest defined by OKPy.
    Instances of this class are callable. When called, it takes
    a global_environment dict, and returns a TestResult object.
    We only take a global_environment, *not* a local_environment.
    This makes tests not useful inside functions, methods or
    other scopes with local variables. This is a limitation of
    doctest, so we roll with it.

    The last 2 attributes (passed, failed_test) are set after calling run().

    Args:
        name (str): Name of test
        tests (:obj:`list` of :obj:`str`): List of docstring tests to be run
        value (int, optional): Point value of this test, defaults to 1
        hidden (bool, optional): Set true if this test should be hidden

    Attributes:
        name (str): Name of test
        tests (:obj:`list` of :obj:`str`): List of docstring tests to be run
        value (int): Point value of this test object, defaults to 1
        hidden (bool): True if this test should be hidden
        passed (bool): True if all tests passed
        failed_test (str): Docstring of first failed test, if any

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

    plain_result_fail_template = Template("""   {{ name }}

Test result:
{{test_result}}""")

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

    def __init__(self, name, tests, value=1, hidden=True):
        """
        tests is list of doctests that should be run.
        """
        self.name = name
        self.tests = tests
        self.value = value
        self.hidden = hidden
        self.passed = None
        self.failed_test = None

    def run(self, global_environment):
        """Runs tests on a given global_environment.
        
        Arguments:
            global_environment (dict of str: str): Result of executing a python notebook/script
        
        Returns:
            (bool, OKTest): Whether the test passed and a pointer to the current OKTest object

        """
        for i, t in enumerate(self.tests):
            passed, result = run_doctest(self.name + ' ' + str(i), t, global_environment)
            if not passed:
                self.passed = False
                self.failed_test = t
                self.result = result
                return False, self
        self.passed = True
        return True, self

    @classmethod
    def from_file(cls, path):
        """
        Parse an ok test file & return an OKTest

        Args:
            cls (OKTest): Uses this to create a new OKTest object from the given file
            path (str): Path to ok test file

        Returns:
            OKTest: new OKTest object created from the given file

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

        tests = []

        for i, test_case in enumerate(test_spec['suites'][0]['cases']):
            tests.append(dedent(test_case['code']))

        return cls(path, tests, test_spec.get('points', 1), test_spec.get('hidden', True))

class OKTests:
    """Test Class for Ok-style tests used to grade assignments.
    
    Args:
        test_paths (:obj:`list` of :obj:`str`): List of paths to ok tests
    
    Attributes:
        paths (:obj:`list` of :obj:`str`): List of paths to ok tests
        tests (:obj:`list` of :obj:`OKTest`): List of OKTest objects for each path

    """
    def __init__(self, test_paths):
        self.paths = test_paths
        self.tests = [OKTest.from_file(path) for path in self.paths if "__init__.py" not in path]

    def run(self, global_environment, include_grade=True):
        """Run this object's tests on a given global environment (from running a notebook/script)
        
        Arguments:
            global_environment (dict of str: str): Result of executing a python notebook/script
                see grade.execute_notebook for more
            include_grade (boolean, optional): Set true if grade should be included in result
        
        Returns:
            OKTestsResult: Object resulting from running tests on GLOBAL_ENVIRONMENT, with grade,
                tests passed, and more information.

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
    Displayable result from running OKTests

    Args:
        grade (float): Grade as a decimal in the range [0, 1]
        paths (:obj:`list` of :obj:`str`): List of paths to ok tests
        tests (:obj:`list` of :obj:`OKTest`): List of OKTest objects for each path
        passed_tests (:obj:`list` of :obj:`str`): List of passed test docstrings
        failed_tests (:obj:`list` of :obj:`str`, :obj:`OKTest`): List of failed test docstrings and
            OKTest objects
        include_grade (boolean, optional): Set true if grade should be included in result

    Attributes:
        grade (float): Grade as a decimal in the range [0, 1]
        paths (:obj:`list` of :obj:`str`): List of paths to ok tests
        tests (:obj:`list` of :obj:`OKTest`): List of OKTest objects for each path
        passed_tests (:obj:`list` of :obj:`str`): List of passed test docstrings
        failed_tests (:obj:`list` of :obj:`str`, :obj:`OKTest`): List of failed test docstrings and
            OKTest objects
        include_grade (boolean, optional): Set true if grade should be included in result

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

    def __repr__(self):
        return OKTestsResult.plain_result_template.render(
            grade=self.grade,
            passed_tests=self.passed_tests,
            failed_tests=self.failed_tests,
            tests=self.tests,
            include_grade=self.include_grade
        )

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """Used to generate a dynamic variable name for grading functions

    This function generates a random name using the given length and character set.
    
    Args:
        size (int): Length of output name
        chars (str): Set of characters used to create function name
    
    Returns:
        str: Randomized string name for grading function

    """
    return ''.join(random.choice(chars) for _ in range(size))

def check(test_file_path, global_env=None):
    """
    check global_env against given test_file in oktest format
    If global_env is none, the global environment of the calling
    function is used. The following two calls are equivalent:
    check('tests/q1.py')
    check('tests/q1.py', globals())
    
    Args:
        test_file_path (str): Path to ok test file
        global_env (dict of str: str, optional): A global environment resulting from the execution 
            of a python script or notebook.

    Returns:
        OKTestsResult: result of running the tests in the given global environment.

    """
    tests = OKTests([test_file_path])

    if global_env is None:
        # Get the global env of our callers - one level below us in the stack
        # The grade method should only be called directly from user / notebook
        # code. If some other method is calling it, it should also use the
        # inspect trick to pass in its parents' global env.
        global_env = inspect.currentframe().f_back.f_globals
    return tests.run(global_env, include_grade=False)