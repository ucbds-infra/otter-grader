"""
Gradescope autograder configuration generator for Otter Generate
"""

import os
import json
import shutil
# import subprocess
import zipfile
import tempfile
import pathlib
import pkg_resources

from glob import glob
from subprocess import PIPE
from jinja2 import Template

from .token import APIClient
from ..plugins import PluginCollection
from ..run.run_autograder.constants import DEFAULT_OPTIONS

TEMPLATE_DIR = pkg_resources.resource_filename(__name__, "templates")
MINICONDA_INSTALL_URL = "https://repo.anaconda.com/miniconda/Miniconda3-py37_4.8.3-Linux-x86_64.sh"
OTTER_ENV_NAME = "otter-gradescope-env"
# TEMPLATE_FILE_PATHS = {
#     "setup.sh": os.path.join(TEMPLATES_DIR, "setup.sh"),
#     "requirements.txt": os.path.join(TEMPLATES_DIR, "requirements.txt"),
#     "requirements.r": os.path.join(TEMPLATES_DIR, "requirements.r"),
#     "run_autograder": os.path.join(TEMPLATES_DIR, "run_autograder"),
#     "run_otter.py": os.path.join(TEMPLATES_DIR, "run_otter.py"),
#     "environment.yml":  os.path.join(TEMPLATES_DIR, "environment.yml"),
# }

def main(args, assignment=None):
    """
    Runs ``otter generate autograder``
    """
    # read in otter_config.json
    if args.config is None and os.path.isfile("otter_config.json"):
        args.config = "otter_config.json"

    assert args.config is None or os.path.isfile(args.config), f"Could not find otter configuration file {args.config}"

    if args.config:
        with open(args.config) as f:
            otter_config = json.load(f)
    else:
        otter_config = {}

    options = DEFAULT_OPTIONS.copy()
    options.update(otter_config)

    # update language
    options["lang"] = args.lang.lower()

    template_dir = os.path.join(TEMPLATE_DIR, options["lang"])

    templates = {}
    for fn in os.listdir(template_dir):
        fp = os.path.join(template_dir, fn)
        with open(fp) as f:
            templates[fn] = Template(f.read())
    # for fn, fp in TEMPLATE_FILE_PATHS.items():
    #     with open(fp) as f:
    #         templates[fn] = Template(f.read())

    template_context = {
        "autograder_dir": options['autograder_dir'],
        "otter_env_name": OTTER_ENV_NAME,
        "miniconda_install_url": MINICONDA_INSTALL_URL,
        "ottr_branch": "stable",
    }

    # # format run_autograder
    # run_otter_py = templates["run_otter.py"].render(
    #     # threshold = str(args.threshold),
    #     # points = str(args.points),
    #     # show_stdout = str(args.show_stdout),
    #     # show_hidden = str(args.show_hidden),
    #     # seed = str(args.seed),
    #     # token = str(args.token),
    #     # course_id = str(args.course_id),
    #     # assignment_id = str(args.assignment_id),
    #     # filtering = str(not args.unfiltered_pdfs),
    #     # pagebreaks = str(not args.no_pagebreaks),
    #     # grade_from_log = str(args.grade_from_log),
    #     # serialized_variables = str(args.serialized_variables),
    #     # public_multiplier = str(args.public_multiplier),
    #     # lang = str(args.lang.lower()),
    #     autograder_dir = options['autograder_dir'],
    # )

    # run_autograder = templates["run_autograder"].render(
    #     autograder_dir = options['autograder_dir'],
    #     otter_env_name = OTTER_ENV_NAME,
    # )

    # # format setup.sh
    # setup_sh = templates["setup.sh"].render(
    #     autograder_dir = options['autograder_dir'],
    #     miniconda_install_url = MINICONDA_INSTALL_URL,
    #     ottr_branch = "stable",
    #     otter_env_name = OTTER_ENV_NAME,
    # )

    # environment_yml = templates["environment.yml"].render(
    #     otter_env_name = OTTER_ENV_NAME,
    # )

    plugins = PluginCollection(otter_config.get("plugins", []), None, {})
    plugins.run("during_generate", otter_config, assignment)

    # create tmp directory to zip inside
    with tempfile.TemporaryDirectory() as td:

        # try:
        # copy tests into tmp
        test_dir = os.path.join(td, "tests")
        os.mkdir(test_dir)
        pattern = ("*.py", "*.[Rr]")[options["lang"] == "r"]
        for file in glob(os.path.join(args.tests_path, pattern)):
            shutil.copy(file, test_dir)

        # open requirements if it exists
        requirements = args.requirements
        reqs_filename = f"requirements.{'R' if options['lang'] == 'r' else 'txt'}"
        if requirements is None and os.path.isfile(reqs_filename):
            requirements = reqs_filename
        
        if requirements:
            assert os.path.isfile(requirements), f"Requirements file {requirements} not found"
            f = open(requirements)
        else:
            f = open(os.devnull)

        template_context["other_requirements"] = f.read()
        template_context["overwrite_requirements"] = args.overwrite_requirements

        rendered = {}
        for fn, tmpl in templates.items():
            rendered[fn] = tmpl.render(**template_context)

        # # render the templates
        # python_requirements = templates["requirements.txt"].render(
        #     other_requirements = f.read() if args.lang.lower() == "python" else "",
        #     overwrite_requirements = args.lang.lower() == "python" and args.overwrite_requirements
        # )

        # # reset the stream
        # f.seek(0)

        # r_requirements = templates["requirements.r"].render(
        #     other_requirements = f.read() if args.lang.lower() == "r" else "",
        #     overwrite_requirements = args.lang.lower() == "python" and args.overwrite_requirements

        # )

        # close the stream
        f.close()
        
        # copy requirements into tmp
        # with open(os.path.join(td, "requirements.txt"), "w+") as f:
        #     f.write(python_requirements)

        # with open(os.path.join(td, "requirements.r"), "w+") as f:
        #     f.write(r_requirements)

        # if r_requirements:
        #     with open(os.path.join(td, "requirements.r"), "w+") as f:
        #         f.write(r_requirements)

        # # write setup.sh and run_autograder to tmp
        # with open(os.path.join(td, "setup.sh"), "w+") as f:
        #     f.write(setup_sh)

        # with open(os.path.join(td, "run_autograder"), "w+") as f:
        #     f.write(run_autograder)

        # with open(os.path.join(td, "run_otter.py"), "w+") as f:
        #     f.write(run_otter_py)

        # with open(os.path.join(td, "environment.yml"), "w+") as f:
        #     f.write(environment_yml)

        # for fn, contents in rendered.items():
        #     fp = os.path.join(td, fn)
        #     with open(fp, "w+") as f:
        #         f.write(contents)

        # with open(os.path.join(td, "otter_config.json"), "w+") as f:
        #     json.dump(otter_config, f, indent=2)

        if os.path.isabs(args.output_path):
            zip_path = os.path.join(args.output_path, "autograder.zip")
        else:
            zip_path = os.path.join(os.getcwd(), args.output_path, "autograder.zip")
        
        if os.path.exists(zip_path):
            os.remove(zip_path)

        with zipfile.ZipFile(zip_path, mode="w") as zf:
            for fn, contents in rendered.items():
                zf.writestr(fn, contents)

            test_dir = "tests"
            pattern = ("*.py", "*.[Rr]")[options["lang"] == "r"]
            for file in glob(os.path.join(args.tests_path, pattern)):
                zf.write(file, arcname=os.path.join(test_dir, os.path.basename(file)))
            
            zf.writestr("otter_config.json", json.dumps(otter_config, indent=2))

            # copy files into tmp
            if len(args.files) > 0:
                # files_basedir = os.path.join(td, "files")
                # os.mkdir(files_basedir)

                for file in args.files:
                    full_fp = os.path.abspath(file)
                    assert os.getcwd() in full_fp, f"{file} is not in a subdirectory of the working directory"
                    zf.write(file, arcname=os.path.join("files", file))




                    # if a directory, copy the entire dir
                    # if os.path.isdir(file):
                    #     shutil.copytree(file, os.path.join(files_basedir, os.path.basename(file)))
                    # else:
                    #     # check that file is in subdir
                    #     file = os.path.abspath(file)
                    #     assert os.getcwd() in file, f"{file} is not in a subdirectory of the working directory"
                    #     wd_path = pathlib.Path(os.getcwd())
                    #     file_path = pathlib.Path(file)
                    #     rel_path = file_path.parent.relative_to(wd_path)
                    #     output_path = os.path.join(files_basedir, rel_path)
                    #     os.makedirs(output_path, exist_ok=True)
                    #     shutil.copy(file, output_path)

        # curr_dir = os.getcwd()
        # os.chdir(td)

        

        
        #     # for fn, contents in rendered.items():

        # zip_cmd = ["zip", "-r", zip_path, "run_autograder", "run_otter.py", "requirements.r",
        #         "setup.sh", "requirements.txt", "environment.yml", "tests", "otter_config.json"]
        
        # if r_requirements:
        #     zip_cmd += ["requirements.r"]

        # if args.files:
        #     zip_cmd += ["files"]

        # zipped = subprocess.run(zip_cmd, stdout=PIPE, stderr=PIPE)

        # if zipped.stderr.decode("utf-8"):
        #     raise Exception(zipped.stderr.decode("utf-8"))

        # # move back to tmp parent directory
        # os.chdir(curr_dir)
        
        # except:
        #     # delete tmp directory
        #     shutil.rmtree("tmp")

        #     # raise the exception
        #     raise
        
        # else:
        #     # delete tmp directory
        #     shutil.rmtree("tmp")
