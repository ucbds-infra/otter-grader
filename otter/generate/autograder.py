#################################################
##### Gradescope Generator for Otter-Grader #####
#################################################

import os
import shutil
import subprocess
import pathlib

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
otter-grader==1.0.0.b2
{% endif %}{% if other_requirements %}
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

from otter.generate.run_autograder import main as run_autograder

config = {
    "score_threshold": {{ threshold }},
    "points_possible": {{ points }},
    "show_stdout_on_release": {{ show_stdout }},
    "show_hidden_tests_on_release": {{ show_hidden }},
    "seed": {{ seed }},
    "grade_from_log": {{ grade_from_log }},
    "serialized_variables": {{ serialized_variables }},
    "public_multiplier": {{ public_multiplier }},
    "token": {% if token %}'{{ token }}'{% else %}None{% endif %},
    "course_id": '{{ course_id }}',
    "assignment_id": '{{ assignment_id }}',
    "filtering": {{ filtering }},
    "pagebreaks": {{ pagebreaks }}
}

if __name__ == "__main__":
    run_autograder(config)
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
        public_multiplier = str(args.public_multiplier)
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
                # if a directory, copy the entire dir
                if os.path.isdir(file):
                    shutil.copytree(file, str(dir / os.path.basename(file)))
                else:
                    # check that file is in subdir
                    file = os.path.abspath(file)
                    assert os.getcwd() in file, \
                        f"{file} is not in a subdirectory of the working directory"
                    wd_path = pathlib.Path(os.getcwd())
                    file_path = pathlib.Path(file)
                    rel_path = file_path.parent.relative_to(wd_path)
                    output_path = os.path.join("tmp", "files", rel_path)
                    os.makedirs(output_path, exist_ok=True)
                    shutil.copy(file, output_path)

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
