"""
Gradescope autograder configuration generator for Otter Generate
"""

import os
import shutil
import subprocess
import pathlib
import pkg_resources

from glob import glob
from subprocess import PIPE
from jinja2 import Template

from .token import APIClient

TEMPLATES_DIR = pkg_resources.resource_filename(__name__, "templates")
SETUP_SH_PATH = os.path.join(TEMPLATES_DIR, "setup.sh")
REQUIREMENTS_PATH = os.path.join(TEMPLATES_DIR, "requirements.txt")
RUN_AUTOGRADER_PATH = os.path.join(TEMPLATES_DIR, "run_autograder")
MINICONDA_INSTALL_URL = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"

with open(SETUP_SH_PATH) as f:
    SETUP_SH = Template(f.read())

with open(REQUIREMENTS_PATH) as f:
    REQUIREMENTS = Template(f.read())

with open(RUN_AUTOGRADER_PATH) as f:
    RUN_AUTOGRADER = Template(f.read())

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
        public_multiplier = str(args.public_multiplier),
        autograder_dir = str(args.autograder_dir),
    )

    setup_sh = SETUP_SH.render(
        miniconda_install_url = MINICONDA_INSTALL_URL
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
            f.write(setup_sh)

        with open(os.path.join(os.getcwd(), "tmp", "run_autograder"), "w+") as f:
            f.write(run_autograder)

        # copy files into tmp
        if len(args.files) > 0:
            os.mkdir(os.path.join("tmp", "files"))

            for file in args.files:
                # if a directory, copy the entire dir
                if os.path.isdir(file):
                    shutil.copytree(file, str(os.path.join("tmp", "files", os.path.basename(file))))
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

        zip_path = os.path.join("..", args.output_path, "autograder.zip")
        if os.path.exists(zip_path):
            os.remove(zip_path)

        zip_cmd = ["zip", "-r", zip_path, "run_autograder",
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
