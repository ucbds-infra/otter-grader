"""Autograder configuration generator for Otter-Grader"""

import importlib.resources
import json
import os
import pathlib
import re
import yaml
import zipfile

from dataclasses import dataclass
from glob import glob
from jinja2 import Environment, PackageLoader
from typing import Any, Literal, Optional, TYPE_CHECKING, Union

from .token import APIClient
from .utils import merge_conda_environments, zip_folder
from ..plugins import PluginCollection
from ..run import AutograderConfig
from ..utils import dump_yaml, load_default_file, OTTER_CONFIG_FILENAME
from ..version import __version__


DEFAULT_PYTHON_VERSION = "3.12"
JINJA_ENV = Environment(loader=PackageLoader(__name__), keep_trailing_newline=True)
OTTER_ENV_NAME = "otter-env"
OTTR_VERSION = "1.5.0"
TEMPLATE_DIR = importlib.resources.files(__name__) / "templates"


@dataclass
class CondaEnvironment:

    python_version: str

    is_r: bool

    requirements: list[str]

    overwrite_requirements: bool

    user_environment: Optional[dict[str, Any]]

    exclude_conda_defaults: bool

    def to_dict(self):
        environment: dict[str, Any] = {
            "name": OTTER_ENV_NAME,
            "channels": ["defaults", "conda-forge"],
            "dependencies": [
                f"python={self.python_version}",
                "pip",
                "nb_conda_kernels",
            ],
        }

        if self.exclude_conda_defaults:
            environment["channels"].remove("defaults")

        if self.is_r:
            environment["channels"].append("r")
            environment["dependencies"].extend(
                [
                    "gcc_linux-64",
                    "gxx_linux-64",
                    "libgit2",
                    "libgomp",
                    "r-base>=4.0.0",
                    "r-devtools",
                    "r-essentials",
                    "r-gert",
                    "r-rmarkdown",
                    "r-startup",
                    "r-stringi",
                    "r-testthat",
                    "r-usethis",
                    f"r-ottr=={OTTR_VERSION}",
                ]
            )

        r_extra = ""
        if self.is_r:
            r_extra = ",r"

        pip_deps = (
            self.requirements
            if self.overwrite_requirements
            else [
                f"otter-grader[grading,plugins{r_extra}]=={__version__}",
                *self.requirements,
            ]
        )

        environment["dependencies"].append({"pip": pip_deps})

        if self.user_environment:
            environment = merge_conda_environments(
                self.user_environment, environment, OTTER_ENV_NAME
            )

        return environment

    def to_str(self):
        return dump_yaml(self.to_dict(), indent=2)


COMMON_TEMPLATES = [
    "common/run_autograder",
    "common/run_otter.py",
]

LANGUAGE_BASED_CONFIGURATIONS = {
    "python": {
        "test_file_pattern": "*.py",
        "requirements_filename": "requirements.txt",
        "templates": [*COMMON_TEMPLATES, "python/setup.sh"],
    },
    "r": {
        "test_file_pattern": "*.[Rr]",
        "requirements_filename": "requirements.R",
        "templates": [*COMMON_TEMPLATES, "r/setup.sh"],
    },
}


def main(
    *,
    tests_dir: str = "./tests",
    output_path: str = "autograder.zip",
    config: Optional[str] = None,
    no_config: bool = False,
    lang: Optional[Union[Literal["python"], Literal["r"]]] = None,
    requirements: Optional[str] = None,
    no_requirements: bool = False,
    overwrite_requirements: bool = False,
    environment: Optional[str] = None,
    no_environment: bool = False,
    username: Optional[str] = None,
    password: Optional[str] = None,
    token: Optional[str] = None,
    files: Optional[list[str]] = None,
    assignment: Optional["Assignment"] = None,
    plugin_collection: Optional[PluginCollection] = None,
    python_version: Optional[str] = None,
    channel_priority_strict: bool = True,
    exclude_conda_defaults: bool = False,
):
    """
    Run Otter Generate.

    Args:
        tests_dir (``str``): path to directory of test files for this assignment
        output_path (``str``): the path at which to write the output zip file
        config (``str``): path to an Otter configuration JSON file
        no_config (``bool``): disables auto-inclusion of Otter config file at ./otter_config.json
        lang (``"python" | "r" | None``): the language of the assignment
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
        files (``list[str] | None``): list of file paths to add to the zip file
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
            if used with Otter Assign
        python_version (``str | None``): the version of Python to use (installed with conda)
        channel_priority_strict (``bool``): whether to set conda's channel_priority to strict in
            the ``setup.sh`` file
        exclude_conda_defaults (``bool``): whether to exclude conda's defaults channel in the
            generated ``environment.yml`` file

    Raises:
        ``FileNotFoundError``: if the specified Otter configuration JSON file could not be found
        ``ValueError``: if the configurations specify a Gradescope course ID or assignment ID but not
            both
    """
    if files is None:
        files = []

    # read in otter config
    if config is None and os.path.isfile(OTTER_CONFIG_FILENAME) and not no_config:
        config = OTTER_CONFIG_FILENAME

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

    elif (
        "token" not in otter_config
        and "course_id" in otter_config
        and "assignment_id" in otter_config
    ):
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
    for template in lang_config["templates"]:
        fn = os.path.basename(template)
        templates[fn] = JINJA_ENV.get_template(template)

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
    with load_default_file(
        requirements,
        lang_config["requirements_filename"],
        default_disabled=no_requirements,
    ) as reqs:
        if reqs is not None:
            if ag_config.lang == "python":
                extra_requirements = [
                    l for l in reqs.split("\n") if l.strip() and not l.strip().startswith("#")
                ]
            elif ag_config.lang == "r":
                r_requirements = reqs
                template_context["has_r_requirements"] = True

    # open environment if it exists
    user_environment = None
    with load_default_file(
        environment, "environment.yml", default_disabled=no_environment
    ) as env_contents:
        template_context["other_environment"] = env_contents
        if env_contents is not None:
            user_environment = yaml.safe_load(env_contents)

    conda_environment = CondaEnvironment(
        python_version or DEFAULT_PYTHON_VERSION,
        ag_config.lang == "r",
        extra_requirements,
        overwrite_requirements,
        user_environment,
        exclude_conda_defaults,
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

        zf.writestr(OTTER_CONFIG_FILENAME, json.dumps(otter_config, indent=2))

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
                    zip_folder(
                        zf, full_fp, prefix=os.path.join("files", os.path.split(relative_fp)[0])
                    )
                else:
                    raise ValueError(f"Could not find file or directory '{full_fp}'")


if TYPE_CHECKING:
    from ..assign import Assignment
