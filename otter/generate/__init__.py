"""Autograder configuration generator for Otter-Grader"""

import json
import os
import pathlib
import pkg_resources
import re
import yaml
import zipfile

from glob import glob
from jinja2 import Template

from .token import APIClient
from .utils import zip_folder

from ..plugins import PluginCollection
from ..run.run_autograder.autograder_config import AutograderConfig
from ..utils import load_default_file


DEFAULT_PYTHON_VERSION = "3.7"
MINICONDA_INSTALL_URL = "https://repo.anaconda.com/miniconda/Miniconda3-py38_4.10.3-Linux-x86_64.sh"
OTTER_ENV_NAME = "otter-env"
OTTR_BRANCH = "v1.2.0"  # this should match a release tag on GitHub
TEMPLATE_DIR = pkg_resources.resource_filename(__name__, "templates")


LANGUAGE_BASED_CONFIGURATIONS = {
    "python": {
        "test_file_pattern": "*.py",
        "requirements_filename": "requirements.txt",
        "template_dir": os.path.join(TEMPLATE_DIR, "python"),
    },
    "r": {
        "test_file_pattern": "*.[Rr]",
        "requirements_filename": "requirements.R",
        "template_dir": os.path.join(TEMPLATE_DIR, "r"),
    },
}


def main(*, tests_dir="./tests", output_path="autograder.zip", config=None, no_config=False, 
         lang=None, requirements=None, no_requirements=False, overwrite_requirements=False, 
         environment=None, no_environment=False, username=None, password=None, token=None, files=[], 
         assignment=None, plugin_collection=None, python_version=None):
    """
    Runs Otter Generate

    Args:
        tests_dir (``str``): path to directory of test files for this assignment
        output_path (``str``): the path at which to write the output zip file
        config (``str``): path to an Otter configuration JSON file
        no_config (``bool``): disables auto-inclusion of Otter config file at ./otter_config.json
        lang (``str``): the language of the assignment; one of ``["python", "r"]``
        requirements (``str``): path to a Python or R requirements file for this assignment
        no_requirements (``bool``): disables auto-inclusion of requirements file at ./requirements.txt
        overwrite_requirements (``bool``): whether to overwrite the default requirements instead of
            adding to them
        environment (``str``): path to a conda environment file for this assignment
        no_environment (``bool``): whether ``./environment.yml`` should be automatically checked if 
            ``environment`` is unspecified
        username (``str``): a username for Gradescope for generating a token
        password (``str``): a password for Gradescope for generating a token
        token (``str``): a token for Gradescope
        files (``list[str]``): list of file paths to add to the zip file
        assignment (``otter.assign.assignment.Assignment``, optional): the assignment configurations
            if used with Otter Assign
        python_version (``str | None``): the version of Python to use (installed with conda)

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
        with open(config, encoding="utf-8") as f:
            otter_config = json.load(f)
    else:
        otter_config = {}

    # if an empty/null token is specified, delete it
    if "token" in otter_config and not otter_config["token"]:
        otter_config.pop("token")

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

    ag_config = AutograderConfig(otter_config)

    # update language
    if lang is not None:
        ag_config.lang = lang
        otter_config["lang"] = lang

    if ag_config.lang not in LANGUAGE_BASED_CONFIGURATIONS.keys():
        raise ValueError(f"Invalid language specified: {ag_config.lang}")

    lang_config = LANGUAGE_BASED_CONFIGURATIONS[ag_config.lang]

    template_dir = lang_config["template_dir"]

    templates = {}
    for fn in os.listdir(template_dir):
        fp = os.path.join(template_dir, fn)
        if os.path.isfile(fp): # prevents issue w/ finding __pycache__ in template dirs
            with open(fp) as f:
                templates[fn] = Template(f.read())

    if python_version is not None:
        match = re.match(r"(\d+)\.(\d+)(\.\d+)?", python_version)
        if not match:
            raise ValueError("Invalid Python version specified")
        if int(match.group(1)) < 3 or int(match.group(2)) < 6:
            raise ValueError("Otter is only compatible with Python 3.6+")

    template_context = {
        "autograder_dir": ag_config.autograder_dir,
        "otter_env_name": OTTER_ENV_NAME,
        "miniconda_install_url": MINICONDA_INSTALL_URL,
        "ottr_branch": OTTR_BRANCH,
        "channel_priority_strict": ag_config.channel_priority_strict,
        "python_version": python_version or DEFAULT_PYTHON_VERSION,
    }

    if plugin_collection is None:
        plugin_collection = PluginCollection(otter_config.get("plugins", []), None, {})

    else:
        plugin_collection.add_new_plugins(otter_config.get("plugins", []))

    plugin_collection.run("during_generate", otter_config, assignment)

    # open requirements if it exists
    with load_default_file(requirements, lang_config["requirements_filename"], 
                           default_disabled=no_requirements,) as reqs:
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
    for fn, template in templates.items():
        rendered[fn] = template.render(**template_context)

    if os.path.exists(output_path):
        os.remove(output_path)

    with zipfile.ZipFile(output_path, mode="w") as zf:
        for fn, contents in rendered.items():
            zf.writestr(fn, contents)

        arc_test_dir = "tests"
        pattern = lang_config["test_file_pattern"]
        for file in glob(os.path.join(tests_dir, pattern)):
            zf.write(file, arcname=os.path.join(arc_test_dir, os.path.basename(file)))

        zf.writestr("otter_config.json", json.dumps(otter_config, indent=2))

        # copy files into tmp
        if len(files) > 0:
            for file in files:
                full_fp = os.path.abspath(file)
                if os.getcwd() not in full_fp:
                    raise ValueError(f"{file} is not in the working directory")

                relative_fp = pathlib.Path(full_fp).relative_to(pathlib.Path(os.getcwd()))
                if os.path.isfile(full_fp):
                    zf.write(file, arcname=os.path.join("files", relative_fp))
                elif os.path.isdir(full_fp):
                    zip_folder(zf, full_fp, prefix=os.path.join("files", os.path.split(relative_fp)[0]))
                else:
                    raise ValueError(f"Could not find file or directory '{full_fp}'")

    if assignment is not None:
        assignment._otter_config = otter_config
