"""Autograder configuration generator for Otter-Grader"""

import json
import os
import pathlib
import pkg_resources
import shutil
import tempfile
import yaml
import zipfile

from glob import glob
from jinja2 import Template
from subprocess import PIPE

from .token import APIClient
from .utils import zip_folder

from ..plugins import PluginCollection
from ..run.run_autograder.constants import DEFAULT_OPTIONS
from ..utils import load_default_file


TEMPLATE_DIR = pkg_resources.resource_filename(__name__, "templates")
MINICONDA_INSTALL_URL = "https://repo.anaconda.com/miniconda/Miniconda3-py38_4.10.3-Linux-x86_64.sh"
OTTER_ENV_NAME = "otter-env"
OTTR_BRANCH = "1.0.0"  # this should match a release tag on GitHub


def main(*, tests_path="./tests", output_dir="./", config=None, no_config=False, lang="python", 
         requirements=None, no_requirements=False, overwrite_requirements=False, environment=None, 
         no_environment=False, username=None, password=None, token=None, files=[], assignment=None, 
         plugin_collection=None):
    """
    Runs Otter Generate

    Args:
        tests_path (``str``): path to directory of test files for this assignment
        output_dir (``str``): directory in which to write output zip file
        config (``str``): path to an Otter configuration JSON file
        no_config (``bool``): disables auto-inclusion of Otter config file at ./otter_config.json
        lang (``str``): the language of the assignment; one of ``["python", "r"]``
        requirements (``str``): path to a Python or R requirements file for this assignment
        no_requirements (``bool``): disables auto-inclusion of requirements file at ./requirements.txt
        overwrite_requirements (``bool``): whether to overwrite the default requirements instead of
            adding to them
        environment (``str``): path to a conda environment file for this assignment
        no_environment (``bool``): whether ``./evironment.yml`` should be automatically checked if 
            ``environment`` is unspecified
        username (``str``): a username for Gradescope for generating a token
        password (``str``): a password for Gradescope for generating a token
        token (``str``): a token for Gradescope
        files (``list[str]``): list of file paths to add to the zip file
        assignment (``otter.assign.assignment.Assignment``, optional): the assignment configurations
            if used with Otter Assign
        **kwargs: ignored kwargs (a remnant of how the argument parser is built)

    Raises:
        ``FileNotFoundError``: if the specified Otter configuration JSON file could not be found
        ``ValueError``: if the configurations specify a Gradescope course ID or assignment ID but not
            both
    """
    # read in otter_config.json
    if config is None and os.path.isfile("otter_config.json") and not no_config:
        config = "otter_config.json"

    if config is not None and not os.path.isfile(config):
        raise FileNotFoundError(f"Could not find otter configuration file {config}")

    if config:
        with open(config) as f:
            otter_config = json.load(f)
    else:
        otter_config = {}

    # ensure that a token is present if necessary
    if "token" not in otter_config and token is not None:
        otter_config["token"] = token
    
    elif "token" not in otter_config and "course_id" in otter_config and "assignment_id" in otter_config:
        client = APIClient()
        if username is not None and password is not None:
            client.log_in(username, password)
            token = client.token
        else:
            token = client.get_token()
        otter_config["token"] = token
    
    elif ("course_id" in otter_config) ^ ("assignment_id" in otter_config):
        raise ValueError(f"Otter config contains 'course_id' or 'assignment_id' but not both")

    options = DEFAULT_OPTIONS.copy()
    options.update(otter_config)

    # update language
    options["lang"] = lang.lower()

    template_dir = os.path.join(TEMPLATE_DIR, options["lang"])

    templates = {}
    for fn in os.listdir(template_dir):
        fp = os.path.join(template_dir, fn)
        if os.path.isfile(fp): # prevents issue w/ finding __pycache__ in template dirs
            with open(fp) as f:
                templates[fn] = Template(f.read())

    template_context = {
        "autograder_dir": options['autograder_dir'],
        "otter_env_name": OTTER_ENV_NAME,
        "miniconda_install_url": MINICONDA_INSTALL_URL,
        "ottr_branch": OTTR_BRANCH,
    }

    if plugin_collection is None:
        plugin_collection = PluginCollection(otter_config.get("plugins", []), None, {})
    else:
        plugin_collection.add_new_plugins(otter_config.get("plugins", []))
    
    plugin_collection.run("during_generate", otter_config, assignment)

    # create tmp directory to zip inside
    with tempfile.TemporaryDirectory() as td:

        # try:
        # copy tests into tmp
        test_dir = os.path.join(td, "tests")
        os.mkdir(test_dir)
        pattern = ("*.py", "*.[Rr]")[options["lang"] == "r"]
        for file in glob(os.path.join(tests_path, pattern)):
            shutil.copy(file, test_dir)

        # open requirements if it exists
        with load_default_file(
            requirements, 
            f"requirements.{'R' if options['lang'] == 'r' else 'txt'}", 
            default_disabled=no_requirements
        ) as reqs:
            template_context["other_requirements"] = reqs if reqs is not None else ""

        template_context["overwrite_requirements"] = overwrite_requirements

        # open environment if it exists
        # unlike requirements.txt, we will always overwrite, not append by default
        with load_default_file(environment, "environment.yml", default_disabled=no_environment) as env_contents:
            template_context["other_environment"] = env_contents
            if env_contents is not None:
                data = yaml.safe_load(env_contents)
                data['name'] = template_context["otter_env_name"]
                template_context["other_environment"] = yaml.safe_dump(data, default_flow_style=False)
  
        rendered = {}
        for fn, tmpl in templates.items():
            rendered[fn] = tmpl.render(**template_context)

        if os.path.isabs(output_dir):
            zip_path = os.path.join(output_dir, "autograder.zip")
        else:
            zip_path = os.path.join(os.getcwd(), output_dir, "autograder.zip")
        
        if os.path.exists(zip_path):
            os.remove(zip_path)

        with zipfile.ZipFile(zip_path, mode="w") as zf:
            for fn, contents in rendered.items():
                zf.writestr(fn, contents)

            test_dir = "tests"
            pattern = ("*.py", "*.[Rr]")[options["lang"] == "r"]
            for file in glob(os.path.join(tests_path, pattern)):
                zf.write(file, arcname=os.path.join(test_dir, os.path.basename(file)))
            
            zf.writestr("otter_config.json", json.dumps(otter_config, indent=2))

            # copy files into tmp
            if len(files) > 0:
                for file in files:
                    full_fp = os.path.abspath(file)
                    assert os.getcwd() in full_fp, f"{file} is not in a subdirectory of the working directory"
                    if os.path.isfile(full_fp):
                        zf.write(file, arcname=os.path.join("files", file))
                    elif os.path.isdir(full_fp):
                        zip_folder(zf, full_fp, prefix="files")
                    else:
                        raise ValueError(f"Could not find file or directory '{full_fp}'")
    
    if assignment is not None:
        assignment._otter_config = otter_config
