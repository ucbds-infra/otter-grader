"""Autograder configuration generator for Otter-Grader"""

import click
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

from ..cli import cli
from ..plugins import PluginCollection
from ..run.run_autograder.constants import DEFAULT_OPTIONS
from ..utils import load_default_file


TEMPLATE_DIR = pkg_resources.resource_filename(__name__, "templates")
MINICONDA_INSTALL_URL = "https://repo.anaconda.com/miniconda/Miniconda3-py38_4.10.3-Linux-x86_64.sh"
OTTER_ENV_NAME = "otter-env"
OTTR_BRANCH = "1.0.0.b0"  # this should match a release tag on GitHub


def main(tests_path, output_path, config, lang, requirements, overwrite_requirements, environment,
         no_env, username, password, files, assignment=None, plugin_collection=None, **kwargs):
    """
    Runs Otter Generate

    Args:
        tests_path (``str``): path to directory of test files for this assignment
        output_path (``str``): directory in which to write output zip file
        config (``str``): path to an Otter configuration JSON file
        lang (``str``): the language of the assignment; one of ``["python", "r"]``
        requirements (``str``): path to a Python or R requirements file for this assignment
        overwrite_requirements (``bool``): whether to overwrite the default requirements instead of
            adding to them
        environment (``str``): path to a conda environment file for this assignment
        no_env (``bool``): whether ``./evironment.yml`` should be automatically checked if 
            ``environment`` is unspecified
        username (``str``): a username for Gradescope for generating a token
        password (``str``): a password for Gradescope for generating a token
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
    if config is None and os.path.isfile("otter_config.json"):
        config = "otter_config.json"

    if config is not None and not os.path.isfile(config):
        raise FileNotFoundError(f"Could not find otter configuration file {config}")

    if config:
        with open(config) as f:
            otter_config = json.load(f)
    else:
        otter_config = {}
    
    if "course_id" in otter_config and "assignment_id" in otter_config:
        client = APIClient()
        if username is not None and password is not None:
            client.log_in(username, password)
            token = client.token
        else:
            token = client.get_token()
        otter_config["token"] = token
    elif "course_id" in otter_config or "assignment_id" in otter_config:
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
        with load_default_file(requirements, f"requirements.{'R' if options['lang'] == 'r' else 'txt'}") as reqs:
            template_context["other_requirements"] = reqs if reqs is not None else ""

        template_context["overwrite_requirements"] = overwrite_requirements

        # open environment if it exists
        # unlike requirements.txt, we will always overwrite, not append by default
        with load_default_file(environment, "environment.yml", default_disabled=no_env) as env_contents:
            template_context["other_environment"] = env_contents
            if env_contents is not None:
                data = yaml.safe_load(env_contents)
                data['name'] = template_context["otter_env_name"]
                template_context["other_environment"] = yaml.safe_dump(data, default_flow_style=False)
  
        rendered = {}
        for fn, tmpl in templates.items():
            rendered[fn] = tmpl.render(**template_context)

        if os.path.isabs(output_path):
            zip_path = os.path.join(output_path, "autograder.zip")
        else:
            zip_path = os.path.join(os.getcwd(), output_path, "autograder.zip")
        
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


@cli.command("generate")
@click.option("-t", "--tests-path", default="./tests/", type=click.Path(exists=True, file_okay=False), help="Path to test files")
@click.option("-o", "--output-path", default="./", type=click.Path(exists=True, file_okay=False), help="Path to which to write zipfile")
@click.option("-c", "--config", default=None, type=click.Path(exists=True, file_okay=False), help="Path to otter configuration file; ./otter_config.json automatically checked")
@click.option("-r", "--requirements", default=None, type=click.Path(exists=True, file_okay=False), help="Path to requirements.txt file; ./requirements.txt automatically checked")
@click.option("--overwrite-requirements", is_flag=True, help="Overwrite (rather than append to) default requirements for Gradescope; ignored if no REQUIREMENTS argument")
@click.option("-e", "--environment", default=None, type=click.Path(exists=True, file_okay=False), help="Path to environment.yml file; ./environment.yml automatically checked (overwrite)")
@click.option("--no-env", is_flag=True, help="Whether to ignore an automatically found but unspecified environment.yml file")
@click.option("-l", "--lang", default="python", type=click.Choice(["python", "r"], case_sensitive=False), help="Assignment programming language; defaults to Python")
@click.option("--autograder-dir", default="/autograder", type=click.Path(), help="Root autograding directory inside grading container")
@click.option("--username", default=None, help="Gradescope username for generating a token")
@click.option("--password", default=None, help="Gradescope password for generating a token")
@click.argument("files", nargs=-1, help="Other support files needed for grading (e.g. .py files, data files)")
def generate_cli(*args, **kwargs):
    """
    Generate a zip file to configure an Otter autograder, including FILES as support files.
    """
    return main(*args, **kwargs)
