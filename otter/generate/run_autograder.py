"""
Gradescope autograding internals
"""

import json
import os
import shutil
import subprocess
import re
import pickle
import warnings
import jupytext
import pandas as pd

from glob import glob
from textwrap import dedent

from .constants import DEFAULT_OPTIONS
from .token import APIClient
from .utils import replace_notebook_instances

from ..check.logs import Log, QuestionNotInLogException
from ..check.notebook import _OTTER_LOG_FILENAME
from ..execute import grade_notebook
from ..export import export_notebook
from ..version import LOGO_WITH_VERSION

def run_r_autograder(config):
    """
    """
    from rpy2.robjects import r

    options = DEFAULT_OPTIONS.copy()
    options.update(config)

    os.chdir(options["autograder_dir"])

    if options["token"] is not None:
        client = APIClient(token=options["token"])
        generate_pdf = True
    else:
        generate_pdf = False

    # put files into submission directory
    if os.path.exists("./source/files"):
        for file in os.listdir("./source/files"):
            fp = os.path.join("./source/files", file)
            if os.path.isdir(fp):
                shutil.copytree(fp, os.path.join("./submission", os.path.basename(fp)))
            else:
                shutil.copy(fp, "./submission")

    os.chdir("./submission")

    # convert ipynb files to Rmd files
    if glob("*.ipynb"):
        fp = glob("*.ipynb")[0]
        nb = jupytext.read(fp)
        jupytext.write(nb, os.path.splitext(fp)[0] + ".Rmd")
    
    # convert Rmd files to R files
    if glob("*.Rmd"):
        fp = glob("*.Rmd")[0]
        fp, wp = os.path.abspath(fp), os.path.abspath(os.path.splitext(fp)[0] + ".r")
        r(f"knitr::purl('{fp}', '{wp}')")

    # get the R script
    fp = glob("*.[Rr]")[0]

    os.makedirs("./tests", exist_ok=True)
    tests_glob = glob("../source/tests/*.[Rr]")
    for file in tests_glob:
        shutil.copy(file, "./tests")

    if os.path.isfile(_OTTER_LOG_FILENAME):
        log = Log.from_file(_OTTER_LOG_FILENAME, ascending=False)
        if options["grade_from_log"]:
            print("\n\n")     # for logging in otter.execute.execute_log
    else:
        assert not options["grade_from_log"], "missing log"
        log = None

    # grading_script = dedent(f"""\
    #     ottr::run_gradescope("{fp}")
    # """)
    output = r(f"""ottr::run_gradescope("{fp}")""")[0]
    output = json.loads(output)
    
    if options["show_stdout_on_release"]:
        output["stdout_visibility"] = "after_published"

    os.chdir(options["autograder_dir"])

    with open("./results/results.json", "w+") as f:
        json.dump(output, f, indent=4)

    print("\n\n")
    print(dedent("""\
    Test scores are summarized in the table below. Passed tests appear as a single cell with no output.
    Failed public tests appear as a single cell with the output of the failed test. Failed hidden tests
    appear as two cells, one with no output (the public tests) and another with the output of the failed
    (hidden) test that is not visible to the student.
    """))
    df = pd.DataFrame(output["tests"])
    if "output" in df.columns:
        df.drop(columns=["output"], inplace=True)
    # df.drop(columns=["hidden"], inplace=True)
    print(df)

def main(config):
    """
    Runs autograder on Gradescope based on predefined configurations.

    Args:
        config (``dict``): configurations for autograder
    """
    print(LOGO_WITH_VERSION, "\n")

    options = DEFAULT_OPTIONS.copy()
    options.update(config)

    # add miniconda back to path
    os.environ["PATH"] = f"{options['miniconda_path']}/bin:" + os.environ.get("PATH")
    
    os.chdir(options["autograder_dir"])

    if options["lang"] == "r":
        run_r_autograder(config)
        return

    if options["token"] is not None:
        client = APIClient(token=options["token"])
        generate_pdf = True
    else:
        generate_pdf = False

    # put files into submission directory
    if os.path.exists("./source/files"):
        for file in os.listdir("./source/files"):
            fp = os.path.join("./source/files", file)
            if os.path.isdir(fp):
                if not os.path.exists(os.path.join("./submission", os.path.basename(fp))):
                    shutil.copytree(fp, os.path.join("./submission", os.path.basename(fp)))
            else:
                shutil.copy(fp, "./submission")

    # create __init__.py files
    subprocess.run(["touch", "./__init__.py"])
    subprocess.run(["touch", "./submission/__init__.py"])

    os.makedirs("./submission/tests", exist_ok=True)
    tests_glob = glob("./source/tests/*.py")
    for file in tests_glob:
        shutil.copy(file, "./submission/tests")

    os.chdir("./submission")

    nb_path = glob("*.ipynb")[0]

    replace_notebook_instances(nb_path)

    # if glob("*.otter"):
    #     assert len(glob("*.otter")) == 1, "Too many .otter files (max 1 allowed)"
    #     with open(glob("*.otter")[0]) as f:
    #         otter_config = json.load(f)
    # else:
    #     otter_config = None

    if os.path.isfile(_OTTER_LOG_FILENAME):
        log = Log.from_file(_OTTER_LOG_FILENAME, ascending=False)
        if options["grade_from_log"]:
            print("\n\n")     # for logging in otter.execute.execute_log
    else:
        assert not options["grade_from_log"], "missing log"
        log = None

    scores = grade_notebook(
        nb_path, 
        glob("./tests/*.py"), 
        name="submission", 
        cwd=".", 
        test_dir="./tests",
        ignore_errors=not options["debug"], 
        seed=options["seed"],
        log=log if options["grade_from_log"] else None,
        variables=options["serialized_variables"]
    )

    # verify the scores against the log
    print("\n\n")
    if log is not None:
        try:
            found_discrepancy = scores.verify_against_log(log)
            if not found_discrepancy:
                print("No discrepancies found while verifying scores against the log.")
        except BaseException as e:
            print(f"Error encountered while trying to verify scores with log:\n{e}")
    else:
        print("No log found with which to verify student scores")

    if generate_pdf:
        try:
            export_notebook(nb_path, filtering=options["filtering"], pagebreaks=options["pagebreaks"])
            pdf_path = os.path.splitext(nb_path)[0] + ".pdf"

            # get student email
            with open("../submission_metadata.json") as f:
                metadata = json.load(f)

            student_emails = []
            for user in metadata["users"]:
                student_emails.append(user["email"])
            
            for student_email in student_emails:
                client.upload_pdf_submission(options["course_id"], options["assignment_id"], student_email, pdf_path)

            print("\n\nSuccessfully uploaded submissions for: {}".format(", ".join(student_emails)))

        except:
            print("\n\n")
            warnings.warn("PDF generation or submission failed", RuntimeWarning)

    output = scores.to_gradescope_dict(config)

    os.chdir(options["autograder_dir"])

    with open("./results/results.json", "w+") as f:
        json.dump(output, f, indent=4)

    print("\n\n")
    df = pd.DataFrame(output["tests"])
    if "output" in df.columns:
        df.drop(columns=["output"], inplace=True)
    # df.drop(columns=["hidden"], inplace=True)
    print(df)