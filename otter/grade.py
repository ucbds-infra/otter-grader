#!/usr/bin/env python

import argparse
import os
from os.path import isfile, join
from glob import glob
from gofer import ok
from gofer.notebook import *
from gofer.utils import hide_outputs
import pandas as pd
import nb2pdf
import re
import json
import itertools

# copied from https://github.com/data-8/Gofer-Grader/blob/master/gofer/ok.py#L210
def grade_notebook(notebook_path, tests_glob=None, name=None, ignore_errors=True, script=False):
    """
    Grade a notebook file & return grade
    """
    # ensure this is not being executed inside a notebook
    try:
        __IPYTHON__
        assert False, "Cannot execute inside Jupyter Notebook"
    except NameError:
        pass

    if not script:
        with open(notebook_path) as f:
            nb = json.load(f)
    else:
        with open(notebook_path) as f:
            nb = f.read()

    secret = ok.id_generator()
    results_array = "check_results_{}".format(secret)
    initial_env = {
        results_array: []
    }

    if name:
        initial_env["__name__"] = name

    if script:
        global_env = execute_script(nb, secret, initial_env, ignore_errors=ignore_errors)
    else:
        global_env = execute_notebook(nb, secret, initial_env, ignore_errors=ignore_errors)

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
                extra_tests.append(ok.OKTests([t]))
        extra_results = [t.run(global_env, include_grade=False) for t in extra_tests]
        test_results += extra_results

    score_mapping = {}
    for r in test_results:
        try:
            for test in r.tests:
                test_name = os.path.split(test.name)[1][:-3]
                score_mapping[test_name] = r.grade
        except IndexError:
            pass

    # add in total score and avoid divide by zero error if there are no tests
    total_score = sum([r.grade for r in test_results])/max(len(test_results), 1)
    score_mapping["total"] = total_score

    return score_mapping

def grade(ipynb_path, pdf, script):
    # get path of notebook file
    base_path = os.path.dirname(ipynb_path)

    # glob tests
    test_files = glob('/home/tests/*.py')

    # get score
    result = grade_notebook(ipynb_path, test_files, script=script)

    # output PDF
    if pdf:
        nb2pdf.convert(ipynb_path)

    return result

def execute_script(script, secret='secret', initial_env=None, ignore_errors=False):
    """
    Execute script & return the global environment that results from execution.
    If ignore_errors is True, exceptions are swallowed.
    secret contains random digits so check_results and check are not easily modifiable
    script is passed in as a string
    """
    with hide_outputs():
        if initial_env:
            global_env = initial_env.copy()
        else:
            global_env = {}
        source = ""
        try:
            exec(script, global_env)
            source += nb
        except:
            if not ignore_errors:
                raise
        tree = ast.parse(source)
        if find_check_assignment(tree) or find_check_definition(tree):
            # an empty global_env will fail all the tests
            return global_env
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
    # implement argparser

    argparser = argparse.ArgumentParser()
    argparser.add_argument('notebook_directory', help='Path to directory with ipynb\'s to grade')
    argparser.add_argument("--pdf", action="store_true", default=False)
    argparser.add_argument("--scripts", action="store_true", default=False)
    args = argparser.parse_args()

    # get all ipynb files
    dir_path = os.path.abspath(args.notebook_directory)
    os.chdir(dir_path)
    file_extension = (".py", ".ipynb")[not args.scripts]
    all_ipynb = [(f, join(dir_path, f)) for f in os.listdir(dir_path) if isfile(join(dir_path, f)) and f.endswith(file_extension)]
    print(all_ipynb)

    all_results = {"file": [], "score": [], "manual": []}

    if not args.pdf:
        del all_results["manual"]

    for ipynb_name, ipynb_path in all_ipynb:
        all_results["file"].append(ipynb_name)
        score = grade(ipynb_path, args.pdf, args.scripts)
        all_results["score"].append(score)
        if args.pdf:
            pdf_path = re.sub(r"\.ipynb$", ".pdf", ipynb_path)
            all_results["manual"].append(pdf_path)

    # expand mappings in all_results["score"]
    print(all_results)
    for q in all_results["score"][0].keys():
        all_results[q] = []

    for score in all_results["score"]:
        for q in score:
            all_results[q] += [score[q]]

    del all_results["score"]

    final_results = pd.DataFrame(all_results)
    final_results.to_csv("grades.csv", index=False)

if __name__ == "__main__":
    main()
