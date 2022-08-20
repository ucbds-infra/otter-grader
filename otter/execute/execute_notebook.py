"""Execution of a Jupyter Notebook"""

import copy
import os
import tempfile

from contextlib import redirect_stdout, redirect_stderr
from IPython.display import display

try:
    from IPython.core.inputtransformer2 import TransformerManager
    _IPYTHON_7 = True
except ImportError:
    from IPython.core.inputsplitter import IPythonInputSplitter
    _IPYTHON_7 = False

from .transforms import create_collected_check_cell

from ..utils import id_generator


def execute_notebook(nb, check_results_list_name="check_results_secret", initial_env=None, 
                     ignore_errors=False, cwd=None, test_dir=None, seed=None, seed_variable=None):
    """
    Execute a notebook and return the global environment that results from execution.

    If ``ignore_errors`` is true, exceptions are swallowed.

    Args:
        nb (``nbformat.NotebookNode``): the notebook to execute
        check_results_list_name (``str``, optional): the name of the list to collect check results in
        initial_env (``dict``, optional): an initial environment
        ignore_errors (``bool``, optional): whether exceptions should be ignored
        cwd (``str``, optional): working directory of execution to be appended to ``sys.path`` in 
            grading environment
        test_dir (``str``, optional): path to directory of tests in grading environment
        seed (``int``, optional): random seed for intercell seeding
        seed_variable (``str``, optional): a variable name to override with the seed

    Results:
        ``dict``: global environment resulting from executing all code of the input notebook
    """
    if initial_env:
        global_env = initial_env.copy()

    else:
        global_env = {}

    # add display from IPython
    global_env["display"] = display

    test_dir = test_dir if test_dir is not None else './tests'

    from ..check.notebook import Notebook
    with Notebook.grading_mode(tests_dir = test_dir if test_dir is not None else './tests') as check_results:
        # add dummy Notebook class so that we can collect results
        secret = id_generator()
        notebook_class_name = f"Notebook_{secret}"
        global_env[notebook_class_name] = Notebook

        source = ""

        if cwd:
            source = f"import sys\nsys.path.append(r\"{cwd}\")\n"
            exec(source, global_env)

        if seed is not None and seed_variable is None:
            import numpy as np
            import random
            global_env["np"] = np
            global_env["random"] = random

        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                if _IPYTHON_7:
                    isp = TransformerManager()

                else:
                    isp = IPythonInputSplitter(line_input_checker=False)

                try:
                    code_lines = []
                    cell_source_lines = cell['source']
                    # TODO: use otter.utils.get_source
                    source_is_str_bool = False
                    if isinstance(cell_source_lines, str):
                        source_is_str_bool = True
                        cell_source_lines = cell_source_lines.split('\n')

                    for line in cell_source_lines:
                        if not line.startswith('%') and  "interact(" not in line:
                            code_lines.append(line)
                            if source_is_str_bool:
                                code_lines.append('\n')

                    # TODO: move to helper function
                    if seed is not None:
                        if seed_variable is None:
                            cell_source = f"np.random.seed({seed})\nrandom.seed({seed})\n" + \
                                isp.transform_cell(''.join(code_lines))

                        else:
                            cell_source = f"{seed_variable} = {seed}\n" + \
                                isp.transform_cell(''.join(code_lines))

                    else:
                        cell_source = isp.transform_cell(''.join(code_lines))

                    with open(os.devnull, 'w') as f, redirect_stdout(f), redirect_stderr(f):
                        exec(cell_source, global_env)

                    source += cell_source

                except:
                    if not ignore_errors:
                        raise

            # add any required checks from this cell
            source += create_collected_check_cell(cell, notebook_class_name, test_dir)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as ntf:
            ntf.write(source)
            ntf.seek(0)

            try:
                cleaned_source = compile(source, filename=ntf.name, mode="exec")
                with open(os.devnull, 'w') as f, redirect_stdout(f), redirect_stderr(f):
                    exec(cleaned_source, global_env)

            except:
                if not ignore_errors:
                    raise

        # add the collected results to the global env
        global_env[check_results_list_name] = check_results

    return global_env
