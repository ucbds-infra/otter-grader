"""Autograder configuration generator for Otter-Grader"""

import json
import os
import pathlib
import pkg_resources
import re
import yaml
import zipfile

from dataclasses import dataclass
from glob import glob
from jinja2 import Template
from typing import Any, Dict, List, Optional

from .token import APIClient
from .utils import merge_conda_environments, zip_folder

from ..plugins import PluginCollection
from ..run.run_autograder.autograder_config import AutograderConfig
from ..utils import dump_yaml, load_default_file
from ..version import __version__


DEFAULT_PYTHON_VERSION = "3.9"
OTTER_ENV_NAME = "otter-env"
OTTR_VERSION = "1.2.0"
TEMPLATE_DIR = pkg_resources.resource_filename(__name__, "templates")
GENERAL_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, "general")


@dataclass
class CondaEnvironment:

    python_version: str

    is_r: bool

    requirements: List[str]

    overwrite_requirements: bool

    user_environment: Optional[Dict[str, Any]]

    def to_dict(self):
        environment = {
            "name": OTTER_ENV_NAME,
            "channels": ["defaults", "conda-forge"],
            "dependencies": [
                f"python={self.python_version}",
                "pip",
                "nb_conda_kernels",
            ],
        }

        if self.is_r:
            environment["channels"].append("r")
            environment["dependencies"].extend([
                "r-base>=4.0.0",
                "r-essentials",
                "r-devtools",
                "libgit2",
                "libgomp",
                "r-gert",
                "r-usethis",
                "r-testthat",
                "r-startup",
                "r-rmarkdown",
                "r-stringi",
            ])

        pip_deps = self.requirements if self.overwrite_requirements else [
            "datascience",
            "jupyter_client", 
            "ipykernel", 
            "matplotlib", 
            "pandas", 
            "ipywidgets", 
            "scipy", 
            "seaborn", 
            "scikit-learn", 
            "jinja2", 
            "nbconvert", 
            "nbformat", 
            "dill",
            "numpy",
            "gspread",
            "pypdf",
            f"otter-grader=={__version__}",
            *self.requirements,
        ]

        environment["dependencies"].append({"pip": pip_deps})

        if self.is_r:
            environment["dependencies"][-1]["pip"].append("rpy2")

        if self.user_environment:
            environment = merge_conda_environments(
                self.user_environment, environment, OTTER_ENV_NAME)

        return environment

    def to_str(self):
        return dump_yaml(self.to_dict(), indent=2)
        # return yaml.safe_dump(self.to_dict(), sort_keys=False, indent=2)


COMMON_TEMPLATES = [
    os.path.join(TEMPLATE_DIR, "common", "run_autograder"),
    os.path.join(TEMPLATE_DIR, "common", "run_otter.py"),
]

LANGUAGE_BASED_CONFIGURATIONS = {
    "python": {
        "test_file_pattern": "*.py",
        "requirements_filename": "requirements.txt",
        "templates": [*COMMON_TEMPLATES, os.path.join(TEMPLATE_DIR, "python", "setup.sh")]
    },
    "r": {
        "test_file_pattern": "*.[Rr]",
        "requirements_filename": "requirements.R",
        "templates": [*COMMON_TEMPLATES, os.path.join(TEMPLATE_DIR, "r", "setup.sh")]
    },
}


def main(*, tests_dir="./tests", output_path="autograder.zip", config=None, no_config=False, 
         lang=None, requirements=None, no_requirements=False, overwrite_requirements=False, 
         environment=None, no_environment=False, username=None, password=None, token=None, files=[], 
         assignment=None, plugin_collection=None, python_version=None, channel_priority_strict=True):
    """
    Run Otter Generate.

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
        channel_priority_strict (``bool``): whether to set conda's channel_priority to strict in
            the ``setup.sh`` file

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

    templates = {}
    for template_path in lang_config["templates"]:
        fn = os.path.basename(template_path)
        with open(template_path) as f:
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
        "ottr_version": OTTR_VERSION,
        "channel_priority_strict": channel_priority_strict,
        "has_r_requirements": False,
    }

    if plugin_collection is None:
        plugin_collection = PluginCollection(otter_config.get("plugins", []), None, {})

    else:
        plugin_collection.add_new_plugins(otter_config.get("plugins", []))

    plugin_collection.run("during_generate", otter_config, assignment)

    # open requirements if it exists
    extra_requirements, r_requirements = [], None
    with load_default_file(requirements, lang_config["requirements_filename"], 
                           default_disabled=no_requirements,) as reqs:
        if reqs is not None:
            if ag_config.lang == "python":
                extra_requirements = [l for l in reqs.split("\n") if l.strip() and not l.strip().startswith("#")]
            elif ag_config.lang == "r":
                r_requirements = reqs
                template_context["has_r_requirements"] = True

    # open environment if it exists
    user_environment = None
    with load_default_file(environment, "environment.yml", default_disabled=no_environment) as env_contents:
        template_context["other_environment"] = env_contents
        if env_contents is not None:
            user_environment = yaml.safe_load(env_contents)

    conda_environment = CondaEnvironment(
        python_version or DEFAULT_PYTHON_VERSION,
        ag_config.lang == "r",
        extra_requirements,
        overwrite_requirements,
        user_environment,
    )

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

        if r_requirements is not None:
            zf.writestr("requirements.r", r_requirements)

        zf.writestr("environment.yml", conda_environment.to_str())

        zf.writestr("otter_config.json", json.dumps(otter_config, indent=2))

        # copy files into zip file
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
