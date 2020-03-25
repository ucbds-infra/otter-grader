#################################################
##### Gradescope Generator for Otter-Grader #####
#################################################

import os
import shutil
import argparse
import subprocess
import sys

from glob import glob
from subprocess import PIPE
from jinja2 import Template

REQUIREMENTS = Template("""datascience
jupyter_client
ipykernel
matplotlib
pandas
ipywidgets
scipy
seaborn
sklearn
jinja2
nb2pdf
tornado==5.1.1
otter-grader==0.4.7{% if other_requirements %}
{{ other_requirements }}{% endif %}
""")

SETUP_SH = """#!/usr/bin/env bash

apt-get install -y python3.7 python3-pip

update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

pip3 install -r /autograder/source/requirements.txt
"""

RUN_AUTOGRADER = Template("""#!/usr/bin/env python3

from otter.execute import grade_notebook
from glob import glob
import json
import os
import shutil
import subprocess
import re
import pandas as pd

SCORE_THRESHOLD = {{ threshold }}
POINTS_POSSIBLE = {{ points }}
SHOW_ALL_ON_RELEASE = {{ show_all }}

UTILS_IMPORT_REGEX = r"\\"from utils import [\\w\\*, ]+"
NOTEBOOK_INSTANCE_REGEX = r"otter.Notebook\\(.+\\)"

if __name__ == "__main__":
    # put files into submission directory
    if os.path.exists("/autograder/source/files"):
        for filename in glob("/autograder/source/files/*.*"):
            shutil.copy(filename, "/autograder/submission")

    # create __init__.py files
    subprocess.run(["touch", "/autograder/__init__.py"])
    subprocess.run(["touch", "/autograder/submission/__init__.py"])

    os.chdir("/autograder/submission")

    # check for *.ipynb.json files
    jsons = glob("*.ipynb.json")
    for file in jsons:
        shutil.copy(file, file[:-5])

    # check for *.ipynb.html files
    htmls = glob("*.ipynb.html")
    for file in htmls:
        shutil.copy(file, file[:-5])

    nb_path = glob("*.ipynb")[0]

    # fix utils import
    try:
        with open(nb_path) as f:
            contents = f.read()
    except UnicodeDecodeError:
        with open(nb_path, "r", encoding="utf-8") as f:
            contents = f.read()

    # contents = re.sub(UTILS_IMPORT_REGEX, "\\"from .utils import *", contents)
    contents = re.sub(NOTEBOOK_INSTANCE_REGEX, "otter.Notebook()", contents)

    try:
        with open(nb_path, "w") as f:
            f.write(contents)
    except UnicodeEncodeError:
        with open(nb_path, "w", encoding="utf-8") as f:
            f.write(contents)

    try:
        os.mkdir("/autograder/submission/tests")
    except FileExistsError:
        pass

    tests_glob = glob("/autograder/source/tests/*.py")
    for file in tests_glob:
        shutil.copy(file, "/autograder/submission/tests")

    scores = grade_notebook(nb_path, tests_glob, name="submission", gradescope=True, ignore_errors=True)
    # del scores["TEST_HINTS"]

    failed_test_output = "Failed Tests:"
    output = {"tests" : []}
    for key in scores:
        if key != "total" and key != "possible":
            output["tests"] += [{
                "name" : key,
                "score" : scores[key]["score"],
                "possible": scores[key]["possible"],
                "visibility": ("visible", "hidden")[scores[key]["hidden"]]
            }]
            if "hint" in scores[key]:
                output["tests"][-1]["output"] = repr(scores[key]["hint"])
    # output["visibility"] = "hidden"
    
    if SHOW_ALL_ON_RELEASE:
        output["stdout_visibility"] = "after_published"

    if POINTS_POSSIBLE is not None:
        output["score"] = scores["total"] / scores["possible"] * POINTS_POSSIBLE

    if SCORE_THRESHOLD is not None:
        if scores["total"] / scores["possible"] >= SCORE_THRESHOLD:
            output["score"] = POINTS_POSSIBLE or scores["possible"]
        else:
            output["score"] = 0

    with open("/autograder/results/results.json", "w+") as f:
        json.dump(output, f, indent=4)

    print("\\n\\n")
    df = pd.DataFrame(output["tests"])
    if "output" in df.columns:
        df.drop(columns=["output"], inplace=True)
    # df.drop(columns=["hidden"], inplace=True)
    print(df)
""")

def main(args):
    """
    Main function for configuring a Gradescope based autograder.
    """
    assert args.threshold is None or 0 <= args.threshold <= 1, "{} is not a valid threshold".format(
        args.threshold
    )

    # format run_autograder
    run_autograder = RUN_AUTOGRADER.render(
        threshold = str(args.threshold),
        points = str(args.points),
        show_all = str(args.show_results)
    )

    # create tmp directory to zip inside
    os.mkdir("./tmp")

    # copy tests into tmp
    os.mkdir(os.path.join("tmp", "tests"))
    for file in glob(os.path.join(args.tests_path, "*.py")):
        shutil.copy(file, os.path.join("tmp", "tests"))

    if os.path.isfile(args.requirements):
        with open(args.requirements) as f:
            requirements = REQUIREMENTS.render(
                other_requirements = f.read()
            )
    elif args.requirements != "requirements.txt":
        assert False, "requirements file {} not found".format(args.requirements)
    else:
        requirements = REQUIREMENTS.render(
            other_requirements = ""
        )

    # copy requirements into tmp
    with open(os.path.join(os.getcwd(), "tmp", "requirements.txt"), "w+") as f:
        f.write(requirements)

    # write setup.sh and run_autograder to tmp
    with open(os.path.join(os.getcwd(), "tmp", "setup.sh"), "w+") as f:
        f.write(SETUP_SH)

    with open(os.path.join(os.getcwd(), "tmp", "run_autograder"), "w+") as f:
        f.write(run_autograder)

    # copy files into tmp
    if len(args.files) > 0:
        os.mkdir(os.path.join("tmp", "files"))

        for file in args.files:
            if file == "gen":
                continue
            shutil.copy(file, os.path.join(os.getcwd(), "tmp", "files"))

    os.chdir("./tmp")

    zip_cmd = ["zip", "-r", os.path.join("..", args.output_path, "autograder.zip"), "run_autograder",
               "setup.sh", "requirements.txt", "tests"]

    if args.files:
        zip_cmd += ["files"]

    zipped = subprocess.run(zip_cmd, stdout=PIPE, stderr=PIPE)

    if zipped.stderr.decode("utf-8"):
        raise Exception(zipped.stderr.decode("utf-8"))

    # move back to tmp parent directory
    os.chdir("..")

    # delete tmp directory
    shutil.rmtree("tmp")

if __name__ == "__main__":
    main()
