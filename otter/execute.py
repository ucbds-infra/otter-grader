########################################################
##### Notebook and File Execution for Otter-Grader #####
########################################################

import os
import re
import json
import ast
import math
import itertools
import inspect
import pprint

from collections import namedtuple
from unittest import mock
from contextlib import redirect_stdout, redirect_stderr
from IPython import get_ipython
from IPython.display import display
try:
    from IPython.core.inputsplitter import IPythonInputSplitter
except ImportError:
    raise ImportError('IPython needs to be installed for notebook grading')

from .logs import QuestionNotInLogException
from .ok_parser import OKTests, CheckCallWrapper
from .utils import hide_outputs, id_generator

TestResult = namedtuple("TestResult", ["name", "score", "possible", "test", "hidden", "incorrect"])

class GradingResults:
    """
    Stores and wrangles test result objects. Initialize with a list of ``otter.ok_parser.OKTestsResult``
    objects and this class will store the results as named tuples so that they can be accessed/manipulated
    easily. Also contains methods to put the results into a nice ``dict`` format or into the correct
    format for Gradescope.

    Args:
        results (``list`` of ``otter.ok_parser.OKTestsResult``): the list of grading results
    
    Attributes:
        raw_results (``list`` of ``otter.ok_parser.OKTestsResult``): the results passed to the constructor
        results (``dict``): maps test names to ``TestResult`` named tuples containing the test result
            information
        total (numeric): the total points earned by the submission
        possible (numeric): the total points possible based on the tests
        tests (``list`` of ``str``): list of test names according to the keys of ``results``
    """
    def __init__(self, results):
        self.raw_results = results
        self.results = {}
        
        total_score, points_possible = 0, 0
        for result in results:
            for test in result.tests:
                test_name = os.path.splitext(os.path.basename(test.name))[0]
                tr = TestResult(
                    name = test_name,
                    score = result.grade * test.value,
                    possible = test.value,
                    test = test,
                    hidden = False,
                    incorrect = False
                )
                self.results[test_name] = tr

                total_score += result.grade * test.value
                points_possible += test.value

            for test, test_obj in result.failed_tests:
                test_name = os.path.splitext(os.path.basename(test.name))[0]
                if test_name in self.results:
                    self.results[test_name] = self.results[test_name]._replace(
                        hidden = test_obj.failed_test_hidden,
                        incorrect = True
                    )
                else:
                    self.results[test_name] = TestResult(
                        name = test_name,
                        score = 0,
                        possible = test.value,
                        test = test,
                        hidden = test_obj.failed_test_hidden,
                        incorrect = True
                    )
        
        self.total = total_score
        self.possible = points_possible
    
    def __repr__(self):
        return pprint.pformat(self.to_dict(), indent=2)

    @property
    def tests(self):
        return list(self.results.keys())
    
    def get_result(self, test_name):
        """
        Returns the ``TestResult`` named tuple corresponding to the test with name ``test_name``

        Args:
            test_name (``str``): the name of the desired test
        
        Returns:
            ``TestResult``: the results of that test
        """
        return self.results[test_name]

    def get_score(self, test_name):
        """
        Returns the score of a test tracked by these results

        Args:
            test_name (``str``): the name of the test
        
        Returns:
            ``int`` or ``float``: the score
        """
        result = self.results[test_name]
        return result.score

    def get_public_score(self, test_name):
        """
        Returns the score of a question based on only public tests. Assumes that all public tests in
        a test file occur before the first hidden tests (because test execution stops at the first
        failed test).

        Args:
            test_name (``str``): the name of the test
        
        Returns:
            ``int`` or ``float``: the score based only on public tests
        """
        result = self.results[test_name]
        if not result.incorrect:
            return result.possible
        elif result.hidden:
            return result.possible
        else:
            return result.score

    def verify_against_log(self, log, ignore_hidden=True):
        """
        Verifies these scores against the results stored in this log using the results returned by 
        ``Log.get_results`` for comparison. Prints a message if the scores differ by more than the 
        default tolerance of ``math.isclose``. If ``ignore_hidden`` is ``True``, hidden tests are
        ignored when verifying scores.

        Args:
            log (``otter.logs.Log``): the log to verify against
            ignore_hidden  (``bool``, optional): whether to ignore hidden tests during verification

        Returns:
            ``bool``: whether a discrepancy was found
        """
        found_discrepancy = False
        for test_name in  self.tests:
            if ignore_hidden:
                score = self.get_public_score(test_name)
            else:
                score = self.get_score(test_name)
            try:
                result = log.get_results(test_name)
                logged_score = result.grade * result.tests[0].value
                if not math.isclose(score, logged_score):
                    print("Score for {} ({:.3f}) differs from logged score ({:.3f})".format(
                        test_name, score, logged_score
                    ))
                    found_discrepancy = True
            except QuestionNotInLogException:
                print(f"No score for {test_name} found in this log")
                found_discrepancy = True
        return found_discrepancy

    def to_dict(self):
        """
        Converts these results into a dictinary, extending the fields of the named tuples in ``results``
        into key, value pairs in a ``dict``.

        Returns:
            ``dict``: the results in dictionary form
        """
        output = {}
        for test_name in self.tests:
            result = self.get_result(test_name)
            output[test_name] = dict(result._asdict())

        return output

    def to_gradescope_dict(self, config={}):
        """
        Converts these results into a dictionary formatted for Gradescope's autograder. Requires a 
        dictionary of configurations for the Gradescope assignment generated using Otter Generate.

        Args:
            config (``dict``): the grading configurations

        Returns:
            ``dict``: the results formatted for Gradescope
        """
        output = {"tests": []}

        # hidden visibility determined by show_hidden_tests_on_release
        hidden_test_visibility = ("hidden", "after_published")[config.get("show_hidden_tests_on_release", False)]
        no_separate_visibility = config.get("test_visibility", "hidden")
        assert no_separate_visibility in ["hidden", "visible", "after_published"]

        for test_name in self.tests:
            result = self.get_result(test_name)
            hidden, incorrect = result.hidden, result.incorrect
            score, possible = result.score, result.possible
            public_score, hidden_score = score * config.get("public_multiplier", 0), score * (1 - config.get("public_multiplier", 0))
            public_possible, hidden_possible = possible * config.get("public_multiplier", 0), possible * (1 - config.get("public_multiplier", 0))
        
            if hidden and incorrect:
                public_score, hidden_score = possible * config.get("public_multiplier", 0), 0
            elif not hidden and incorrect:
                public_score, hidden_score = 0, 0
                public_possible = possible
            
            if config.get("separate_tests", True):
                output["tests"].append({
                    "name": result.name + " - Public",
                    "score": public_score,
                    "max_score": public_possible,
                    "visibility": "visible",
                    "output": repr(result.test) if not hidden and incorrect else "All tests passed!"
                })

                if not (not hidden and incorrect):
                    output["tests"].append({
                        "name" : result.name + " - Hidden",
                        "score" : hidden_score,
                        "max_score": hidden_possible,
                        "visibility": hidden_test_visibility,
                        "output": repr(result.test) if incorrect else "All tests passed!"
                    })
            
            else:
                output["tests"].append({
                    "name": result.name,
                    "score": score,
                    "max_score": possible,
                    "visibility": no_separate_visibility,
                    "output": repr(result.test) if not hidden and incorrect else "All tests passed!"
                })
        
        if config.get("show_stdout_on_release", False):
            output["stdout_visibility"] = "after_published"

        if config.get("points_possible", None) is not None:
            output["score"] = self.total / self.possible * config.get("points_possible", None)

        if config.get("score_threshold", None) is not None:
            if self.total / self.possible >= config["score_threshold"]:
                output["score"] = config.get("points_possible", None) or self.possible
            else:
                output["score"] = 0
        
        return output

def check(test_file_path, global_env=None):
    """
    Checks ``global_env`` against given ``test_file`` in OK-format. If global_env is ``None``, the 
    global environment of the calling function is used. The following two calls are equivalent:

    .. code-block:: python
        check('tests/q1.py')
        check('tests/q1.py', globals())
    
    Args:
        test_file_path (``str``): path to test file
        global_env (``dict``, optional): a global environment resulting from the execution 
            of a python script or notebook

    Returns:
        ``otter.ok_parser.OKTestsResult``: result of running the tests in the given global environment

    """
    tests = OKTests([test_file_path])

    if global_env is None:
        # Get the global env of our callers - one level below us in the stack
        # The grade method should only be called directly from user / notebook
        # code. If some other method is calling it, it should also use the
        # inspect trick to pass in its parents' global env.
        global_env = inspect.currentframe().f_back.f_globals

    return tests.run(global_env, include_grade=False)

def grade_notebook(notebook_path, tests_glob=None, name=None, ignore_errors=True, script=False, 
    cwd=None, test_dir=None, seed=None, log=None, variables=None):
    """
    Grade a notebook file & return grade information

    This function grades a single Jupyter notebook using the provided tests. If grading a Python file,
    set ``script`` to true. 

    Args:
        notebook_path (``str``): path to a single notebook
        tests_glob (``list`` of ``str``, optional): names of test files
        name (``str``, optional): initial environment name
        ignore_errors (``bool``, optional): whether errors in execution should be ignored
        script (``bool``, optional): whether the notebook_path is a Python script
        cwd (``str``, optional): working directory of execution to be appended to ``sys.path`` in 
            grading environment
        test_dir (``str``, optional): path to directory of tests in grading environment
        seed (``int``, optional): random seed for intercell seeding
        log (``otter.logs.Log``, optional): log from which to grade questions
        variables (``dict``, optional): map of variable names -> type string to check type of deserialized
            object to prevent arbitrary code from being put into the environment; ignored if log is ``None``

    Returns:
        ``GradingResults``: the results of grading
    """
    # ensure this is not being executed inside a notebook
    assert get_ipython() is None, "Cannot execute inside Jupyter Notebook"

    if not script:
        try:
            with open(notebook_path) as f:
                nb = json.load(f)
        except UnicodeDecodeError:
            with open(notebook_path, encoding='utf-8') as f:
                nb = json.load(f)
    else:
        with open(notebook_path) as f:
            nb = f.read()

    secret = id_generator()
    results_array = "check_results_{}".format(secret)
    initial_env = {
        results_array: []
    }

    if name:
        initial_env["__name__"] = name

    if log is not None:
        global_env = execute_log(nb, log, secret, initial_env, ignore_errors=ignore_errors, cwd=cwd, test_dir=test_dir, variables=variables)
    elif script:
        global_env = execute_script(nb, secret, initial_env, ignore_errors=ignore_errors, cwd=cwd, seed=seed)
    else:
        global_env = execute_notebook(nb, secret, initial_env, ignore_errors=ignore_errors, cwd=cwd, test_dir=test_dir, seed=seed)

    test_results = global_env[results_array]

    # Check for tests which were not included in the notebook and specified by tests_globs
    # Allows instructors to run notebooks with additional tests not accessible to user
    if tests_glob:
        # unpack list of paths into a single list
        tested_set = list(itertools.chain(*[r.paths for r in test_results]))
        extra_tests = []
        for t in sorted(tests_glob):
            include = True
            for tested in tested_set:
                if tested in t:     # e.g. if 'tests/q1.py' is in /srv/repo/lab01/tests/q1.py'
                    include = False
            if include:
                extra_tests.append(OKTests([t]))
        extra_results = [t.run(global_env, include_grade=False) for t in extra_tests]
        test_results += extra_results

    # score_mapping = {}
    # points_possible, total_score = 0, 0
    # for r in test_results:
    #     try:
    #         for test in r.tests:
    #             test_name = os.path.split(test.name)[1][:-3]
    #             score_mapping[test_name] = {
    #                 "score": r.grade * test.value,
    #                 "possible": test.value,
    #                 "test": test,
    #                 # "hidden": test.hidden
    #             }
    #             total_score += r.grade * test.value
    #             points_possible += test.value
    #         for tup in r.failed_tests:
    #             test_name = os.path.split(tup[0].name)[1][:-3]
    #             if test_name in score_mapping:
    #                 score_mapping[test_name]["hint"] = tup[1]#.__repr__()
    #                 score_mapping[test_name]["hidden"] = tup[1].failed_test_hidden
    #             else:
    #                 score_mapping[test_name] = {
    #                     "hint": tup[1],#.__repr__()
    #                     "hidden": tup[1].failed_test_hidden,
    #                     "test": tup[0],
    #                 }
    #     except IndexError:
    #         pass

    # # add in total score and avoid divide by zero error if there are no tests
    # score_mapping["total"] = total_score
    # score_mapping["possible"] = points_possible

    # return score_mapping

    return GradingResults(test_results)

def execute_log(nb, log, secret='secret', initial_env=None, ignore_errors=False, cwd=None, test_dir=None, variables=None):
    """
    Executes a notebook from logged environments and returns the global environment that results from execution

    Execute notebook & return the global environment that results from execution. If ``ignore_errors`` 
    is ``True``, exceptions are swallowed. ``secret`` contains random digits so ``check_results`` and 
    ``check`` are not easily modifiable. ``nb`` is passed in as a dictionary that's a parsed notebook

    Args:
        nb (``dict``): JSON representation of a notebook
        log (``otter.logs.Log``): log from notebook execution
        secret (``str``, optional): randomly generated integer used to rebind check function
        initial_env (``str``, optional): name of initial environment
        ignore_errors (``bool``, optional): whether exceptions should be ignored
        cwd (``str``, optional): working directory of execution to be appended to ``sys.path`` in 
            grading environment
        test_dir (``str``, optional): path to directory of tests in grading environment
        variables (``dict``, optional): map of variable names -> type string to check type of deserialized
            object to prevent arbitrary code from being put into the environment
    
    Results:
        ``dict``: global environment resulting from executing all code of the input notebook
    """
    with hide_outputs():
        if initial_env:
            global_env = initial_env.copy()
        else:
            global_env = {}

        if test_dir:
            source = f"import otter\ngrader = otter.Notebook(\"{test_dir}\")\n"
        else:
            source = f"import otter\ngrader = otter.Notebook()\n"
        
        if cwd:
            source +=  f"import sys\nsys.path.append(\"{cwd}\")\n"

        logged_questions = []
        m = mock.mock_open()
        with mock.patch("otter.notebook.Notebook._log_event", m):
            exec(source, global_env)

            for cell in nb['cells']:
                if cell['cell_type'] == 'code':
                    # transform the input to executable Python
                    # FIXME: use appropriate IPython functions here
                    isp = IPythonInputSplitter(line_input_checker=False)
                    
                    code_lines = []
                    cell_source_lines = cell['source']
                    source_is_str_bool = False
                    if isinstance(cell_source_lines, str):
                        source_is_str_bool = True
                        cell_source_lines = cell_source_lines.split('\n')

                    # only execute import statements
                    cell_source_lines = [re.sub(r"^\s+", "", l) for l in cell_source_lines if "import" in l]                                
                    
                    for line in cell_source_lines:
                        try:
                            exec(line, global_env)
                    # source += cell_source
                        except:
                            if not ignore_errors:
                                raise


            for entry in log.question_iterator():
                shelf = entry.unshelve(global_env)

                if variables is not None:
                    for k, v in shelf.items():
                        full_type = type(v).__module__ + "." + type(v).__name__
                        if not (k in variables and variables[k] == full_type):
                            del shelf[k]
                            print(f"Found variable of different type than expected: {k}")

                global_env.update(shelf)
                global_env[f"check_results_{secret}"].append(global_env["grader"].check(entry.question, global_env=global_env))
                logged_questions.append(entry.question)

        print("Questions executed from log: {}".format(", ".join(logged_questions)))
        
        return global_env

def execute_notebook(nb, secret='secret', initial_env=None, ignore_errors=False, cwd=None, test_dir=None, seed=None):
    """
    Executes a notebook and returns the global environment that results from execution

    Execute notebook & return the global environment that results from execution. If ``ignore_errors`` 
    is ``True``, exceptions are swallowed. ``secret`` contains random digits so ``check_results`` and 
    ``check`` are not easily modifiable. ``nb`` is passed in as a dictionary that's a parsed notebook

    Args:
        nb (``dict``): JSON representation of a notebook
        secret (``str``, optional): randomly generated integer used to rebind check function
        initial_env (``str``, optional): name of initial environment
        ignore_errors (``bool``, optional): whether exceptions should be ignored
        cwd (``str``, optional): working directory of execution to be appended to ``sys.path`` in 
            grading environment
        test_dir (``str``, optional): path to directory of tests in grading environment
        seed (``int``, optional): random seed for intercell seeding
    
    Results:
        ``dict``: global environment resulting from executing all code of the input notebook
    """
    with hide_outputs():
        if initial_env:
            global_env = initial_env.copy()
        else:
            global_env = {}

        # add display from IPython
        global_env["display"] = display

        source = ""
        # if gradescope:
        #     source = "import sys\nsys.path.append(\"/autograder/submission\")\n"
        # el
        if cwd:
            source = f"import sys\nsys.path.append(\"{cwd}\")\n"
            exec(source, global_env)
        if seed is not None:
            # source += "import numpy as np\nimport random\n"
            import numpy as np
            import random
            global_env["np"] = np
            global_env["random"] = random

        # Before rewriting AST, find cells of code that generate errors.
        # One round of execution is done beforehand to mimic the Jupyter notebook style of running
        # (e.g. code runs up to the point of execution).
        # The reason this is workaround is introduced is because once the
        # source code is parsed into an AST, there is no sense of local cells

        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                # transform the input to executable Python
                # FIXME: use appropriate IPython functions here
                isp = IPythonInputSplitter(line_input_checker=False)
                try:
                    code_lines = []
                    cell_source_lines = cell['source']
                    source_is_str_bool = False
                    if isinstance(cell_source_lines, str):
                        source_is_str_bool = True
                        cell_source_lines = cell_source_lines.split('\n')

                    for line in cell_source_lines:
                        # Filter out ipython magic commands
                        # Filter out interact widget
                        if not line.startswith('%'):
                            if "interact(" not in line and not re.search(r"otter\.Notebook\(.*?\)", line):
                                code_lines.append(line)
                                if source_is_str_bool:
                                    code_lines.append('\n')
                            elif re.search(r"otter\.Notebook\(.*?\)", line):
                                # TODO: move this check into CheckCallWrapper
                                # if gradescope:
                                #     line = re.sub(r"otter\.Notebook\(.*?\)", "otter.Notebook(\"/autograder/submission/tests\")", line)
                                # el
                                if test_dir:
                                    line = re.sub(r"otter\.Notebook\(.*?\)", f"otter.Notebook(\"{test_dir}\")", line)
                                else:
                                    line = re.sub(r"otter\.Notebook\(.*?\)", "otter.Notebook(\"/home/tests\")", line)
                                code_lines.append(line)
                                if source_is_str_bool:
                                    code_lines.append('\n')
                    if seed is not None:
                        cell_source = "np.random.seed({})\nrandom.seed({})\n".format(seed, seed) + isp.transform_cell(''.join(code_lines))
                    else:
                        cell_source = isp.transform_cell(''.join(code_lines))

                    # patch otter.Notebook.export so that we don't create PDFs in notebooks
                    # TODO: move this patch into CheckCallWrapper
                    m = mock.mock_open()
                    with mock.patch('otter.Notebook.export', m), mock.patch("otter.Notebook._log_event", m):
                        exec(cell_source, global_env)
                    source += cell_source
                except:
                    if not ignore_errors:
                        raise

        tree = ast.parse(source)
        # # CODE BELOW COMMENTED OUT BECAUSE the only check function is within the Notebook class
        # if find_check_assignment(tree) or find_check_definition(tree):
        #     # an empty global_env will fail all the tests
        #     return global_env

        # wrap check(..) calls into a check_results_X.append(check(..))
        transformer = CheckCallWrapper(secret)
        tree = transformer.visit(tree)
        ast.fix_missing_locations(tree)

        cleaned_source = compile(tree, filename="nb-ast", mode="exec")
        try:
            with open(os.devnull, 'w') as f, redirect_stdout(f), redirect_stderr(f):
                # patch otter.Notebook.export so that we don't create PDFs in notebooks
                m = mock.mock_open()
                with mock.patch('otter.Notebook.export', m), mock.patch("otter.Notebook._log_event", m):
                    exec(cleaned_source, global_env)
        except:
            if not ignore_errors:
                raise
        return global_env

def execute_script(script, secret='secret', initial_env=None, ignore_errors=False, cwd=None, test_dir=None, seed=None):
    """
    Executes code of a Python script and returns the resulting global environment

    Execute script & return the global environment that results from execution. If ``ignore_errors`` is 
    ``True``, exceptions are swallowed. ``secret`` contains random digits so ``check_results`` and 
    ``check`` are not easily modifiable. ``script`` is passed in as a string.

    Args:
        script (``str``): string representation of Python script code
        secret (``str``, optional): randomly generated integer used to rebind check function
        initial_env (``str``, optional): name of initial environment
        ignore_errors (``bool``, optional): whether exceptions should be ignored
        cwd (``str``, optional): working directory of execution to be appended to ``sys.path`` in 
            grading environment
        test_dir (``str``, optional): path to directory of tests in grading environment
        seed (``int``, optional): random seed for intercell seeding
    
    Results:
        dict: global environment resulting from executing all code of the input script
    """
    with hide_outputs():
        if initial_env:
            global_env = initial_env.copy()
        else:
            global_env = {}
        source = ""
        # if gradescope:
        #     source = "import sys\nsys.path.append(\"/autograder/submission\")\n"
        # el
        if cwd:
            source =  f"import sys\nsys.path.append(\"{cwd}\")\n"
        if seed is not None:
            # source += "import numpy as np\nimport random\n"
            import numpy as np
            import random
            global_env["np"] = np
            global_env["random"] = random
            source += "np.random.seed({})\nrandom.seed({})\n".format(seed, seed)

        lines = script.split("\n")
        for i, line in enumerate(lines):
            # TODO: move this check into CheckCallWrapper
            if re.search(r"otter\.Notebook\(.*?\)", line):
                # if gradescope:
                #     line = re.sub(r"otter\.Notebook\(.*?\)", "otter.Notebook(\"/autograder/submission/tests\")", line)
                # else:
                if test_dir:
                    line = re.sub(r"otter\.Notebook\(.*?\)", f"otter.Notebook(\"{test_dir}\")", line)
                else:
                    line = re.sub(r"otter\.Notebook\(.*?\)", "otter.Notebook(\"/home/tests\")", line)
            lines[i] = line
        try:
            exec("\n".join(lines), global_env)
            source += "\n".join(lines)
        except:
            if not ignore_errors:
                raise
        
        tree = ast.parse(source)
        # # CODE BELOW COMMENTED OUT BECAUSE the only check function is within the Notebook class
        # if find_check_assignment(tree) or find_check_definition(tree):
        #     # an empty global_env will fail all the tests
        #     return global_env

        # wrap check(..) calls into a check_results_X.append(check(..))
        transformer = CheckCallWrapper(secret)
        tree = transformer.visit(tree)
        ast.fix_missing_locations(tree)
        cleaned_source = compile(tree, filename="nb-ast", mode="exec")
        try:
            with open(os.devnull, 'w') as f, redirect_stdout(f), redirect_stderr(f):
                exec(cleaned_source, global_env)
        except:
            if not ignore_errors:
                raise
        return global_env
