########################################
##### Run Autograder on Gradescope #####
########################################

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

from ..execute import grade_notebook
from ..export import export_notebook
from .token import APIClient
from ..logs import Log, QuestionNotInLogException
from ..notebook import _OTTER_LOG_FILENAME
from ..version import LOGO_WITH_VERSION

NOTEBOOK_INSTANCE_REGEX = r"otter.Notebook\(.+\)"

def main(config):
    """
    Runs autograder on Gradescope based on predefined configurations.

    Args:
        config (``dict``): configurations for autograder
    """
    print(LOGO_WITH_VERSION, "\n")

    if config.get("token", None) is not None:
        client = APIClient(token=config.get("token", None))
        generate_pdf = True
    else:
        generate_pdf = False

    # put files into submission directory
    if os.path.exists("/autograder/source/files"):
        for file in os.listdir("/autograder/source/files"):
            fp = os.path.join("/autograder/source/files", file)
            if os.path.isdir(fp):
                if not os.path.exists(os.path.join("/autograder/submission", os.path.basename(fp))):
                    shutil.copytree(fp, os.path.join("/autograder/submission", os.path.basename(fp)))
            else:
                shutil.copy(fp, "/autograder/submission")

    # create __init__.py files
    subprocess.run(["touch", "/autograder/__init__.py"])
    subprocess.run(["touch", "/autograder/submission/__init__.py"])

    os.chdir("/autograder/submission")

    # # check for *.ipynb.json files
    # jsons = glob("*.ipynb.json")
    # for file in jsons:
    #     shutil.copy(file, file[:-5])

    # # check for *.ipynb.html files
    # htmls = glob("*.ipynb.html")
    # for file in htmls:
    #     shutil.copy(file, file[:-5])

    nb_path = glob("*.ipynb")[0]

    # fix utils import
    try:
        with open(nb_path) as f:
            contents = f.read()
    except UnicodeDecodeError:
        with open(nb_path, "r", encoding="utf-8") as f:
            contents = f.read()
    
    contents = re.sub(NOTEBOOK_INSTANCE_REGEX, "otter.Notebook()", contents)

    try:
        with open(nb_path, "w") as f:
            f.write(contents)
    except UnicodeEncodeError:
        with open(nb_path, "w", encoding="utf-8") as f:
            f.write(contents)

    os.makedirs("/autograder/submission/tests", exist_ok=True)
    tests_glob = glob("/autograder/source/tests/*.py")
    for file in tests_glob:
        shutil.copy(file, "/autograder/submission/tests")

    if glob("*.otter"):
        assert len(glob("*.otter")) == 1, "Too many .otter files (max 1 allowed)"
        with open(glob("*.otter")[0]) as f:
            otter_config = json.load(f)
    else:
        otter_config = None

    if os.path.isfile(_OTTER_LOG_FILENAME):
        log = Log.from_file(_OTTER_LOG_FILENAME, ascending=False)
        if config.get("grade_from_log", False):
            print("\n\n")     # for logging in otter.execute.execute_log
    else:
        assert not config.get("grade_from_log", False), "missing log"
        log = None

    scores = grade_notebook(
        nb_path, 
        glob("/autograder/submission/tests/*.py"), 
        name="submission", 
        cwd="/autograder/submission", 
        test_dir="/autograder/submission/tests",
        ignore_errors=True, 
        seed=config.get("seed", None),
        log=log if config.get("grade_from_log", False) else None,
        variables=config.get("serialized_variables", None)
    )

    # verify the scores against the log
    print("\n\n")
    if log is not None:
        try:
            found_discrepancy = log.verify_scores(scores)
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

    # # hidden visibility determined by show_hidden_tests_on_release
    # hidden_test_visibility = ("hidden", "after_published")[config.get("show_hidden_tests_on_release", False)]

    # output = {"tests" : []}
    # for key in scores:
    #     if key != "total" and key != "possible":
    #         hidden, incorrect = scores[key].get("hidden", False), "hint" in scores[key]
    #         score, possible = scores[key]["score"], scores[key]["possible"]
    #         public_score, hidden_score = score * config.get("public_multiplier", 0), score * (1 - config.get("public_multiplier", 0))
    #         public_possible, hidden_possible = possible * config.get("public_multiplier", 0), possible * (1 - config.get("public_multiplier", 0))

    #         if hidden and incorrect:
    #             public_score, hidden_score = possible * config.get("public_multiplier", 0), 0
    #         elif not hidden and incorrect:
    #             public_score, hidden_score = 0, 0
    #             public_possible = possible
            
    #         output["tests"] += [{
    #             "name" : key + " - Public",
    #             "score" : public_score,
    #             "max_score": public_possible,
    #             "visibility": "visible",
    #             "output": repr(scores[key]["test"]) if not hidden and incorrect else "All tests passed!",
    #         }]
    #         # if not hidden and incorrect:
    #         #     output["tests"][-1]["output"] = repr(scores[key]["hint"])
            
    #         if not (not hidden and incorrect):
    #             output["tests"] += [{
    #                 "name" : key + " - Hidden",
    #                 "score" : hidden_score,
    #                 "max_score": hidden_possible,
    #                 "visibility": hidden_test_visibility,
    #                 "output": repr(scores[key]["test"]) if incorrect else "All tests passed!"
    #             }]
    #             # if hidden and incorrect:
    #             #     output["tests"][-1]["output"] = repr(scores[key]["hint"])
    
    # if config.get("show_stdout_on_release", False):
    #     output["stdout_visibility"] = "after_published"

    # if config.get("points_possible", None) is not None:
    #     output["score"] = scores["total"] / scores["possible"] * config.get("points_possible", None)

    # if config.get("score_threshold", None) is not None:
    #     if scores["total"] / scores["possible"] >= config["score_threshold"]:
    #         output["score"] = config.get("points_possible", None) or scores["possible"]
    #     else:
    #         output["score"] = 0

    with open("/autograder/results/results.json", "w+") as f:
        json.dump(output, f, indent=4)

    print("\n\n")
    # print(dedent("""\
    # Test scores are summarized in the table below. Passed tests appear as a single cell with no output.
    # Failed public tests appear as a single cell with the output of the failed test. Failed hidden tests
    # appear as two cells, one with no output (the public tests) and another with the output of the failed
    # (hidden) test that is not visible to the student.
    # """))
    df = pd.DataFrame(output["tests"])
    if "output" in df.columns:
        df.drop(columns=["output"], inplace=True)
    # df.drop(columns=["hidden"], inplace=True)
    print(df)