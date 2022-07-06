"""Execution of a submission through log deserialization"""

import re

from IPython.core.inputsplitter import IPythonInputSplitter
from unittest import mock

from ..utils import get_variable_type


def execute_log(nb, log, check_results_list_name="check_results_secret", initial_env=None, 
                ignore_errors=False, cwd=None, test_dir=None, variables=None):
    """
    Execute a notebook from logged environments and return the global environment that results.

    If ``ignore_errors`` is true, exceptions are swallowed.

    Args:
        nb (``nbformat.NotebookNode``): the notebook to execute
        log (``otter.check.logs.Log``): log from notebook execution
        check_results_list_name (``str``, optional): the name of the list to collect check results in
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
    with mock.patch("otter.Notebook._log_event", m):
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

                    except:
                        if not ignore_errors:
                            raise

        for entry in log.question_iterator():
            shelf = entry.unshelve(global_env)

            if variables is not None:
                for k, v in shelf.items():
                    full_type = get_variable_type(v)
                    if not (k in variables and variables[k] == full_type):
                        del shelf[k]
                        print(f"Found variable of different type than expected: {k}")

            global_env.update(shelf)
            global_env[check_results_list_name].append(
                global_env["grader"].check(entry.question, global_env=global_env))
            logged_questions.append(entry.question)

    print("Questions executed from log: {}".format(", ".join(logged_questions)))

    return global_env
