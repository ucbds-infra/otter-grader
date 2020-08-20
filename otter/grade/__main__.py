"""
In-container grading interface for Otter Grader
"""

import argparse
import os
import re
import json
import zipfile
import shutil
import tempfile
import pandas as pd

from glob import glob
try:
    from IPython.core.inputsplitter import IPythonInputSplitter
except ImportError:
    raise ImportError('IPython needs to be installed for notebook grading')

from ..execute import grade_notebook
from ..export import export_notebook
from ..utils import id_generator

def grade(ipynb_path, pdf, script, ignore_errors=True, seed=None, cwd=None):
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
        export_notebook(
            ipynb_path, 
            filtering = pdf != "unfiltered", 
            debug=True,
        )

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
    parser.add_argument('submission_directory', help="Path to submissions directory")
    parser.add_argument("--pdfs", default=False, const="unfiltered", choices=["unfiltered", "html"], nargs="?")
    parser.add_argument("--scripts", action="store_true", default=False)
    parser.add_argument("--seed", type=int, default=None, help="A random seed to be executed before each cell")
    parser.add_argument("--zips", action="store_true", default=False, help="Whether the submissions are Notebook.export zip archives")
    parser.add_argument("--verbose", default=False, action="store_true", help="If present prints scores and hints to stdout")
    parser.add_argument("--debug", default=False, action="store_true", help="Does not ignore errors on execution")

    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    # cd into dir containing submissions
    subs_dir = os.path.abspath(args.submission_directory)
    os.chdir(subs_dir)

    # get file extension and get all of those files in dir_path
    file_extension = (".zip", ".py", ".ipynb")[[args.zips, args.scripts, True].index(True)]
    files = [(f, os.path.join(subs_dir, f)) for f in os.listdir(subs_dir) if os.path.splitext(f)[1] == file_extension]

    all_results = {"file": [], "score": [], "manual": []}

    if not args.pdfs:
        del all_results["manual"]

    # if zips, creat subdir to grade in
    if file_extension == ".zip":
        secret = id_generator()
        grading_dir = os.path.join(subs_dir, f"SUBMISSION_GRADING_DIRECTORY_{secret}")

        # copy all support files/folders into a template grading dir which we will copy from 
        # each time we grade a submission
        template_grading_dir = tempfile.mkdtemp()
        for fn in os.listdir(subs_dir):
            fp = os.path.join(subs_dir, fn)
            if os.path.isfile(fp) and os.path.splitext(fp)[1] != file_extension:
                shutil.copy(fp, template_grading_dir)
            elif os.path.isdir(fp):
                shutil.copytree(fp, os.path.join(template_grading_dir, fn))
    
    else:
        grading_dir = None

    # grade files
    for fname, fpath in files:
        os.chdir(subs_dir)

        all_results["file"].append(fname)

        # if zips, extract zip file into grading dir and find the gradeable filename
        if file_extension == ".zip":
            shutil.copytree(template_grading_dir, grading_dir)
            zf = zipfile.ZipFile(fpath)
            zf.extractall(grading_dir)
            os.chdir(grading_dir)
            gradeables = glob(os.path.join(grading_dir, ("*.py", "*.ipynb")[not args.scripts]))
            assert len(gradeables) == 1, f"Wrong number of gradeable files in submission {fname}"
            fpath = gradeables[0]

        # grade the submission
        score = grade(
            fpath, 
            args.pdfs, 
            args.scripts, 
            ignore_errors = not args.debug, 
            seed = args.seed, 
            cwd = grading_dir if grading_dir else subs_dir
        )
        score = score.to_dict()

        if args.verbose:
            print("Score details for {}".format(fname))
            print(json.dumps(score, default=lambda o: repr(o), indent=2))

        all_results["score"].append({t : score[t]["score"] if type(score[t]) == dict else score[t] for t in score})
        
        if args.pdfs:
            pdf_path = os.path.splitext(fpath)[0] + ".pdf"
            all_results["manual"].append(pdf_path)

        if file_extension == ".zip":
            shutil.rmtree(grading_dir)

    os.chdir(subs_dir)

    if file_extension ==  ".zip":
        shutil.rmtree(template_grading_dir)

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
