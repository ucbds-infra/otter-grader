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
import pandas as pd

from glob import glob
from textwrap import dedent

from .token import APIClient
from .utils import replace_notebook_instances

from ..check.logs import Log, QuestionNotInLogException
from ..check.notebook import _OTTER_LOG_FILENAME
from ..execute import grade_notebook
from ..export import export_notebook
from ..version import LOGO_WITH_VERSION


def main(config):
    """
    Runs autograder on Gradescope based on predefined configurations.

    Args:
        config (``dict``): configurations for autograder
    """
    print(LOGO_WITH_VERSION, "\n")
    
    os.chdir(config.get("autograder_dir", "/autograder"))

    if config.get("token", None) is not None:
        client = APIClient(token=config.get("token", None))
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
        if config.get("grade_from_log", False):
            print("\n\n")     # for logging in otter.execute.execute_log
    else:
        assert not config.get("grade_from_log", False), "missing log"
        log = None

    scores = grade_notebook(
        nb_path, 
        glob("./tests/*.py"), 
        name="submission", 
        cwd=".", 
        test_dir="./tests",
        ignore_errors=not config.get("debug", False), 
        seed=config.get("seed", None),
        log=log if config.get("grade_from_log", False) else None,
        variables=config.get("serialized_variables", None)
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
            export_notebook(nb_path, filtering=config.get("filtering"), pagebreaks=config.get("pagebreaks"))
            pdf_path = os.path.splitext(nb_path)[0] + ".pdf"

            # get student email
            with open("../submission_metadata.json") as f:
                metadata = json.load(f)

            student_emails = []
            for user in metadata["users"]:
                student_emails.append(user["email"])
            
            for student_email in student_emails:
                client.upload_pdf_submission(config["course_id"], config["assignment_id"], student_email, pdf_path)

            print("\n\nSuccessfully uploaded submissions for: {}".format(", ".join(student_emails)))

        except:
            print("\n\n")
            warnings.warn("PDF generation or submission failed", RuntimeWarning)

    output = scores.to_gradescope_dict(config)

    os.chdir(config.get("autograder_dir", "/autograder"))

    with open("./results/results.json", "w+") as f:
        json.dump(output, f, indent=4)

    print("\n\n")
    df = pd.DataFrame(output["tests"])
    if "output" in df.columns:
        df.drop(columns=["output"], inplace=True)
    # df.drop(columns=["hidden"], inplace=True)
    print(df)