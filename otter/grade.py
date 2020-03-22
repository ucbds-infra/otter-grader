###########################################
##### Grading Script for Otter-Grader #####
###########################################

import argparse
import os
from os.path import isfile, join
from glob import glob
from otter.gofer import *
import pandas as pd
import nb2pdf
import re
import json
import itertools
from unittest import mock

try:
    from IPython.core.inputsplitter import IPythonInputSplitter
except ImportError:
    raise ImportError('IPython needs to be installed for notebook grading')

# copied from https://github.com/data-8/Gofer-Grader/blob/master/gofer/ok.py#L210
def grade_notebook(notebook_path, tests_glob=None, name=None, ignore_errors=True, script=False, gradescope=False):
    """
    Grade a notebook file & return grade

    This function grades a single ipython notebook using the provided tests. If grading a .py file,
    set script to true. 

    Args:
        notebook_path (str): path to a single notebook
        tests_glob (:obj:`list` of :obj:`str`, optional): names of test files
        name (str, optional): initial environment name
        ignore_errors (bool, optional): whether errors should be ignored, passed as an arg to 
            execute functions
        script (bool, optional): true if the notebook_path is a python script, false if notebook

    Returns:
        dict: a score mapping with values for each test, student score, and total points possible 
    """
    # ensure this is not being executed inside a notebook
    try:
        __IPYTHON__
        assert False, "Cannot execute inside Jupyter Notebook"
    except NameError:
        pass

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

    if script:
        global_env = execute_script(nb, secret, initial_env, ignore_errors=ignore_errors)
    else:
        global_env = execute_notebook(nb, secret, initial_env, ignore_errors=ignore_errors, gradescope=gradescope)

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

    score_mapping = {}
    points_possible, total_score = 0, 0
    for r in test_results:
        try:
            for test in r.tests:
                test_name = os.path.split(test.name)[1][:-3]
                score_mapping[test_name] = {
                    "score": r.grade * test.value,
                    "possible": test.value,
                    "hidden": test.hidden
                }
                total_score += r.grade * test.value
                points_possible += test.value
            for tup in r.failed_tests:
                test_name = os.path.split(tup[0].name)[1][:-3]
                if test_name in score_mapping:
                    score_mapping[test_name]["hint"] = tup[1]#.__repr__()
                else:
                    score_mapping[test_name] = {
                        "hint": tup[1]#.__repr__()
                    }
        except IndexError:
            pass

    # add in total score and avoid divide by zero error if there are no tests
    score_mapping["total"] = total_score
    score_mapping["possible"] = points_possible

    # score_mapping["TEST_HINTS"] = {}
    # points_possible = 0
    # total_score = 0
    # for r in test_results:
    #     try:
    #         for test in r.tests:
    #             test_name = os.path.split(test.name)[1][:-3]
    #             score_mapping[test_name] = r.grade * test.value
    #             total_score += r.grade * test.value
    #             points_possible += test.value
    #         for tup in r.failed_tests:
    #             test_name = os.path.split(tup[0].name)[1][:-3]
    #             score_mapping["TEST_HINTS"][test_name] = tup[1]
    #     except IndexError:
    #         pass

    # # add in total score and avoid divide by zero error if there are no tests
    # score_mapping["total"] = total_score
    # score_mapping["possible"] = points_possible

    return score_mapping

def grade(ipynb_path, pdf, tag_filter, html_filter, script):
    """
    Grades a single ipython notebook and returns the score

    If no PDF is needed, set the pdf, tag_filter, and html_filter parameters to false. For .py
    files, set script to true.

    Args:
        ipynb_path (str): path to the ipython notebook
        pdf (bool): set true if no filtering needed to generate pdf 
        tag_filter (bool): whether cells should be filtered by tag
        html_filter (bool): whether cells should be filtered by comments
        script (bool): whether the input file is a python script

    Returns:
        dict: a score mapping with values for each test, student score, and total points possible 
    """
    # get path of notebook file
    base_path = os.path.dirname(ipynb_path)

    # glob tests
    test_files = glob('/home/tests/*.py')

    # get score
    result = grade_notebook(ipynb_path, test_files, script=script, ignore_errors=True)

    # output PDF
    if pdf:
        nb2pdf.convert(ipynb_path)
    elif tag_filter:
        nb2pdf.convert(ipynb_path, filtering=True, filter_type="tags")
    elif html_filter:
        nb2pdf.convert(ipynb_path, filtering=True, filter_type="html")

    return result

def execute_notebook(nb, secret='secret', initial_env=None, ignore_errors=False, gradescope=False):
    """
    Executes an ipython notebook and return the global environment that results from execution.

    Execute notebook & return the global environment that results from execution.
    TODO: write a note about the injection of check_results
    If ignore_errors is True, exceptions are swallowed.
    secret contains random digits so check_results and check are not easily modifiable
    nb is passed in as a dictionary that's a parsed ipynb file

    Args:
        nb (dict of str: str): json representation of ipython notebook
        secret (str, optional): randomly generated integer used to rebind check function
        initial_env (str, optional): name of initial environment
        ignore_errors (bool, optional): whether exceptions should be ignored
    
    Results:
        dict of str: object: global environment resulting from executing all code of the input notebook
    """
    with hide_outputs():
        if initial_env:
            global_env = initial_env.copy()
        else:
            global_env = {}

        source = ""
        if gradescope:
            source = "import sys\nsys.path.append(\"/autograder/submission\")\n"

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
                                if gradescope:
                                    line = re.sub(r"otter\.Notebook\(.*?\)", "otter.Notebook(\"/autograder/submission/tests\")", line)
                                else:
                                    line = re.sub(r"otter\.Notebook\(.*?\)", "otter.Notebook(\"/home/tests\")", line)
                                code_lines.append(line)
                                if source_is_str_bool:
                                    code_lines.append('\n')
                    cell_source = isp.transform_cell(''.join(code_lines))

                    # patch otter.Notebook.export so that we don't create PDFs in notebooks
                    m = mock.mock_open()
                    with mock.patch('otter.Notebook.export', m):
                        exec(source + cell_source, global_env)
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
                with mock.patch('otter.Notebook.export', m):
                    exec(cleaned_source, global_env)
        except:
            if not ignore_errors:
                raise
        return global_env

def execute_script(script, secret='secret', initial_env=None, ignore_errors=False):
    """
    Executes code of a python (.py) script and returns the resulting global environment

    Execute script & return the global environment that results from execution.
    If ignore_errors is True, exceptions are swallowed.
    secret contains random digits so check_results and check are not easily modifiable
    script is passed in as a string

    Args:
        script (str): string representation of python script code
        secret (str, optional): secret string for naming check function
        initial_env (str, optional): name of initial environment
        ignore_errors (bool): whether exceptions should be ignored
    
    Results:
        dict: global environment resulting from executing all code of the input script
    """
    with hide_outputs():
        if initial_env:
            global_env = initial_env.copy()
        else:
            global_env = {}
        source = ""
        try:
            exec(script, global_env)
            source += script
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

def main():
    """
    When executing this file from the command line, this function will be run.
    """
    # implement argparser

    argparser = argparse.ArgumentParser()
    argparser.add_argument('notebook_directory', help='Path to directory with ipynb\'s to grade')
    argparser.add_argument("--pdf", action="store_true", default=False)
    argparser.add_argument("--tag-filter", action="store_true", default=False)
    argparser.add_argument("--html-filter", action="store_true", default=False)
    argparser.add_argument("--scripts", action="store_true", default=False)

    args = argparser.parse_args()

    # get all ipynb files
    dir_path = os.path.abspath(args.notebook_directory)
    os.chdir(dir_path)
    file_extension = (".py", ".ipynb")[not args.scripts]
    all_ipynb = [(f, join(dir_path, f)) for f in os.listdir(dir_path) if isfile(join(dir_path, f)) and f.endswith(file_extension)]

    all_results = {"file": [], "score": [], "manual": []}

    if not args.pdf and not args.html_filter and not args.tag_filter:
        del all_results["manual"]

    for ipynb_name, ipynb_path in all_ipynb:
        all_results["file"].append(ipynb_name)
        score = grade(ipynb_path, args.pdf, args.tag_filter, args.html_filter, args.scripts)
        # del score["TEST_HINTS"]
        all_results["score"].append({t : score[t]["score"] if type(score[t]) == dict else score[t] for t in score})
        if args.pdf or args.html_filter or args.tag_filter:
            pdf_path = re.sub(r"\.ipynb$", ".pdf", ipynb_path)
            all_results["manual"].append(pdf_path)

    try:
        # expand mappings in all_results["score"]
        for q in all_results["score"][0].keys():
            all_results[q] = []

        for score in all_results["score"]:
            for q in score:
                all_results[q] += [score[q]]#["score"]]

    except IndexError:
        pass

    del all_results["score"]

    final_results = pd.DataFrame(all_results)
    final_results.to_csv("grades.csv", index=False)

if __name__ == "__main__":
    main()
