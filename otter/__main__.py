########################################################
##### Notebook and File Execution for Otter-Grader #####
########################################################

import argparse
import os
import re
import json
import nb2pdf
import pandas as pd

from glob import glob
try:
    from IPython.core.inputsplitter import IPythonInputSplitter
except ImportError:
    raise ImportError('IPython needs to be installed for notebook grading')

from .execute import grade_notebook

def grade(ipynb_path, pdf, tag_filter, html_filter, script, ignore_errors=True, seed=None, cwd=None):
    """
    Grades a single ipython notebook and returns the score

    If no PDF is needed, set the pdf, tag_filter, and html_filter parameters to false. For .py
    files, set script to true.

    Args:
        ipynb_path (``str``): path to the notebook
        pdf (``bool``): whether unfiltered PDFs of notebooks should be generated
        tag_filter (``bool``): whether cell tag-filtered PDFs of notebooks should be generated
        html_filter (``bool``): whether HTML comment-filtered PDFs of notebooks should be generated
        script (``bool``): whether the input file is a Python script
        ignore_errors (``bool``, optional): whether errors should be ignored during execution
        seed (``int``, optional): random seed for intercell seeding
        cwd (``str``, optional): working directory of execution to be appended to ``sys.path`` in 
            grading environment

    Returns:
        ``dict``: a score mapping with keys for each test, the student's scores, and total points 
            earned and possible 
    """
    # # get path of notebook file
    # base_path = os.path.dirname(ipynb_path)

    # glob tests
    test_files = glob('/home/tests/*.py')

    # get score
    result = grade_notebook(ipynb_path, test_files, script=script, ignore_errors=ignore_errors, seed=seed, cwd=cwd)

    # output PDF
    if pdf:
        nb2pdf.convert(ipynb_path)
    elif tag_filter:
        nb2pdf.convert(ipynb_path, filtering=True, filter_type="tags")
    elif html_filter:
        nb2pdf.convert(ipynb_path, filtering=True, filter_type="html")

    return result

def main(args=None):
    """
    Parses command line arguments and executes submissions. Writes grades to a CSV file and optionally
    generates PDFs of submissions.

    Args:
        args (``list`` of ``str``, optional): alternate command line arguments
    """
    # implement argparser
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook_directory', help='Path to directory with ipynb\'s to grade')
    parser.add_argument("--pdf", action="store_true", default=False)
    parser.add_argument("--tag-filter", action="store_true", default=False)
    parser.add_argument("--html-filter", action="store_true", default=False)
    parser.add_argument("--scripts", action="store_true", default=False)
    parser.add_argument("--seed", type=int, default=None, help="A random seed to be executed before each cell")
    parser.add_argument("--verbose", default=False, action="store_true", help="If present prints scores and hints to stdout")
    parser.add_argument("--debug", default=False, action="store_true", help="Does not ignore errors on execution")

    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    # get all ipynb files
    dir_path = os.path.abspath(args.notebook_directory)
    os.chdir(dir_path)
    file_extension = (".py", ".ipynb")[not args.scripts]
    all_ipynb = [(f, os.path.join(dir_path, f)) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)) and f.endswith(file_extension)]

    all_results = {"file": [], "score": [], "manual": []}

    if not args.pdf and not args.html_filter and not args.tag_filter:
        del all_results["manual"]

    for ipynb_name, ipynb_path in all_ipynb:
        all_results["file"].append(ipynb_name)
        score = grade(ipynb_path, args.pdf, args.tag_filter, args.html_filter, args.scripts, ignore_errors=not args.debug, seed=args.seed, cwd=dir_path)
        if args.verbose:
            print("Score details for {}".format(ipynb_name))
            print(json.dumps(score, default=lambda o: repr(o)))
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
