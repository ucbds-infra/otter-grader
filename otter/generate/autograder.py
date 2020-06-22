#################################################
##### Gradescope Generator for Otter-Grader #####
#################################################

import os
import shutil
import subprocess

from glob import glob
from subprocess import PIPE
from jinja2 import Template

from .token import APIClient

REQUIREMENTS = Template("""{% if not overwrite %}datascience
jupyter_client
ipykernel
matplotlib
pandas
ipywidgets
scipy
seaborn
sklearn
jinja2
nbconvert
nbformat
dill
numpy==1.16.0
tornado==5.1.1
git+https://github.com/ucbds-infra/otter-grader.git@8fc89203e2e02819e77addb0f10144a2a119c358{% endif %}{% if other_requirements %}
{{ other_requirements }}{% endif %}
""")

SETUP_SH = """#!/usr/bin/env bash

apt-get install -y python3.7 python3-pip python3.7-dev

# apt install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 \\
#        libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 \\
#        libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 \\
#        libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 \\
#        libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation \\
#        libappindicator1 libnss3 lsb-release xdg-utils wget

apt-get update
apt-get install -y pandoc
apt-get install -y texlive-xetex texlive-fonts-recommended texlive-generic-recommended

update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

pip3 install -r /autograder/source/requirements.txt
"""

RUN_AUTOGRADER = Template("""#!/usr/bin/env python3

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
from nb2pdf import convert

from otter.execute import grade_notebook
from otter.export import export_notebook
from otter.generate.token import APIClient
from otter.logs import Log, QuestionNotInLogException
from otter.notebook import _OTTER_LOG_FILENAME

SCORE_THRESHOLD = {{ threshold }}
POINTS_POSSIBLE = {{ points }}
SHOW_STDOUT_ON_RELEASE = {{ show_stdout }}
SHOW_HIDDEN_TESTS_ON_RELEASE = {{ show_hidden }}
SEED = {{ seed }}
GRADE_FROM_LOG = {{ grade_from_log }}
SERIALIZED_VARIABLES = {{ serialized_variables }}
PUBLIC_TEST_MULTIPLIER = {{ public_test_multiplier }}

# for auto-uploading PDFs
{% if token %}TOKEN = '{{ token }}'{% else %}TOKEN = None{% endif %}
COURSE_ID = '{{ course_id }}'
ASSIGNMENT_ID = '{{ assignment_id }}'
FILTERING = {{ filtering }}
PAGEBREAKS = {{ pagebreaks }}

if TOKEN is not None:
    CLIENT = APIClient(token=TOKEN)
    GENERATE_PDF = True
else:
    GENERATE_PDF = False

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

    if glob("*.otter"):
        assert len(glob("*.otter")) == 1, "Too many .otter files (max 1 allowed)"
        with open(glob("*.otter")[0]) as f:
            config = json.load(f)
    else:
        config = None

    if os.path.isfile(_OTTER_LOG_FILENAME):
        log = Log.from_file(_OTTER_LOG_FILENAME, ascending=False)
        if GRADE_FROM_LOG:
            print("\\n\\n")     # for logging in otter.execute.execute_log
    else:
        assert not GRADE_FROM_LOG, "missing log"
        log = None

    scores = grade_notebook(
        nb_path, 
        glob("/autograder/submission/tests/*.py"), 
        name="submission", 
        cwd="/autograder/submission", 
        test_dir="/autograder/submission/tests",
        ignore_errors=True, 
        seed=SEED,
        log=log if GRADE_FROM_LOG else None
    )
    # del scores["TEST_HINTS"]

    # verify the scores against the log
    print("\\n\\n")
    if log is not None:
        try:
            found_discrepancy = log.verify_scores(scores)
            if not found_discrepancy:
                print("No discrepancies found while verifying scores against the log.")
        except BaseException as e:
            print(f"Error encountered while trying to verify scores with log:\\n{e}")
    else:
        print("No log found with which to verify student scores")

    if GENERATE_PDF:
        try:
            export_notebook(nb_path, filtering=FILTERING, pagebreaks=PAGEBREAKS)
            pdf_path = os.path.splitext(nb_path)[0] + ".pdf"

            # get student email
            with open("../submission_metadata.json") as f:
                metadata = json.load(f)

            student_emails = []
            for user in metadata["users"]:
                student_emails.append(user["email"])
            
            for student_email in student_emails:
                CLIENT.upload_pdf_submission(COURSE_ID, ASSIGNMENT_ID, student_email, pdf_path)

            print("\\n\\nSuccessfully uploaded submissions for: {}".format(", ".join(student_emails)))

        except:
            print("\\n\\n")
            warnings.warn("PDF generation or submission failed", RuntimeWarning)

    # hidden visibility determined by SHOW_HIDDEN_TESTS_ON_RELEASE
    hidden_test_visibility = ("hidden", "after_published")[SHOW_HIDDEN_TESTS_ON_RELEASE]

    output = {"tests" : []}
    for key in scores:
        if key != "total" and key != "possible":
            hidden, incorrect = scores[key].get("hidden", False), "hint" in scores[key]
            score, possible = scores[key]["score"], scores[key]["possible"]
            public_score, hidden_score = score * PUBLIC_TEST_MULTIPLIER, score * (1 - PUBLIC_TEST_MULTIPLIER)
            public_possible, hidden_possible = possible * PUBLIC_TEST_MULTIPLIER, possible * (1 - PUBLIC_TEST_MULTIPLIER)
            
            output["tests"] += [{
                "name" : key + " - Public",
                "score" : (public_score, score)[not hidden and incorrect],
                "max_score": (public_possible, possible)[not hidden and incorrect],
                "visibility": "visible",
                "output": repr(scores[key]["test"]),
            }]
            # if not hidden and incorrect:
            #     output["tests"][-1]["output"] = repr(scores[key]["hint"])
            
            if not (not hidden and incorrect):
                output["tests"] += [{
                    "name" : key + " - Hidden",
                    "score" : (score, hidden_score)[not hidden and incorrect],
                    "max_score": (possible, hidden_possible)[not hidden and incorrect],
                    "visibility": hidden_test_visibility,
                    "output": repr(scores[key]["test"])
                }]
                # if hidden and incorrect:
                #     output["tests"][-1]["output"] = repr(scores[key]["hint"])
    
    if SHOW_STDOUT_ON_RELEASE:
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
    print(dedent(\"\"\"\\
    Test scores are summarized in the table below. Passed tests appear as a single cell with no output.
    Failed public tests appear as a single cell with the output of the failed test. Failed hidden tests
    appear as two cells, one with no output (the public tests) and another with the output of the failed
    (hidden) test that is not visible to the student.
    \"\"\"))
    df = pd.DataFrame(output["tests"])
    if "output" in df.columns:
        df.drop(columns=["output"], inplace=True)
    # df.drop(columns=["hidden"], inplace=True)
    print(df)
""")

def main(args):
    """
    Runs ``otter generate autograder``
    """
    assert args.threshold is None or 0 <= args.threshold <= 1, "{} is not a valid threshold".format(
        args.threshold
    )

    if args.course_id or args.assignment_id:
        assert args.course_id and args.assignment_id, "Either course ID or assignment ID unspecified for PDF submissions"
        if not args.token:
            args.token = APIClient.get_token()

    # check that args.public_multiplier is valid
    assert 0 <= args.public_multiplier <= 1, f"Public test multiplier {args.public_multiplier} is not between 0 and 1"

    # format run_autograder
    run_autograder = RUN_AUTOGRADER.render(
        threshold = str(args.threshold),
        points = str(args.points),
        show_stdout = str(args.show_stdout),
        show_hidden = str(args.show_hidden),
        seed = str(args.seed),
        token = str(args.token),
        course_id = str(args.course_id),
        assignment_id = str(args.assignment_id),
        filtering = str(not args.unfiltered_pdfs),
        pagebreaks = str(not args.no_pagebreaks),
        grade_from_log = str(args.grade_from_log),
        serialized_variables = str(args.serialized_variables),
        public_test_multiplier = str(args.public_multiplier)
    )

    # create tmp directory to zip inside
    os.mkdir("./tmp")

    try:
        # copy tests into tmp
        os.mkdir(os.path.join("tmp", "tests"))
        for file in glob(os.path.join(args.tests_path, "*.py")):
            shutil.copy(file, os.path.join("tmp", "tests"))

        if os.path.isfile(args.requirements):
            with open(args.requirements) as f:
                requirements = REQUIREMENTS.render(
                    overwrite = args.overwrite_requirements,
                    other_requirements = f.read()
                )
        elif args.requirements != "requirements.txt":
            assert False, "requirements file {} not found".format(args.requirements)
        else:
            requirements = REQUIREMENTS.render(
                overwrite = args.overwrite_requirements,
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
                # if file == "gen":
                #     continue
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
    
    except:
        # delete tmp directory
        shutil.rmtree("tmp")

        # raise the exception
        raise
    
    else:
        # delete tmp directory
        shutil.rmtree("tmp")
