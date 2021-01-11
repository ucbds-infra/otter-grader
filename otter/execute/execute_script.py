"""
Execution of a Python script
"""

import os
import re
import ast

from contextlib import redirect_stdout, redirect_stderr

from .check_wrapper import CheckCallWrapper
from ..utils import hide_outputs

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
        ``dict``: global environment resulting from executing all code of the input script
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

