"""Utilities for Otter Assign"""

import copy
import datetime as dt
import json
import os
import pathlib
import re
import shutil

from glob import glob
from textwrap import indent

from ..execute import grade_notebook
from ..generate import main as generate_autograder
from ..utils import get_source, NOTEBOOK_METADATA_KEY


class EmptyCellException(Exception):
    """
    Exception for empty cells to indicate deletion
    """


class AssignNotebookFormatException(Exception):
    """
    """
    def __init__(self, message, question, cell_index, *args, **kwargs):
        message += " ("
        if question is not None:
            message += f"question { question.name }, "
        message += f"cell number { cell_index + 1 })"
        super().__init__(message, *args, **kwargs)


def get_notebook_language(nb):
    """
    Parse the notebook kernel language and return it as a string.

    Args:
        nb (``nbformat.NotebookNode``): the notebook

    Returns:
        ``str``: the name of the language as a lowercased string
    """
    return nb["metadata"]["kernelspec"]["language"].lower()


def is_ignore_cell(cell):
    """
    Returns whether the current cell should be ignored

    Args:
        cell (``nbformat.NotebookNode``): a notebook cell

    Returns:
        ``bool``: whether the cell is a ignored
    """
    source = get_source(cell)
    return bool(source and
        re.match(r"(##\s*ignore\s*##\s*|#\s*ignore\s*)", source[0], flags=re.IGNORECASE))


def is_cell_type(cell, cell_type):
    """
    Determine whether a cell is of a specific type.

    Args:
        cell (``nbformat.NotebookNode``): the cell to check
        cell_type (``str``): the cell type to check for

    Returns:
        ``bool``: whether ``cell`` is of type ``cell_type``        
    """
    return cell["cell_type"] == cell_type


def remove_output(nb):
    """
    Remove all outputs from a notebook in-place.

    Args:
        nb (``nbformat.NotebookNode``): a notebook
    """
    for cell in nb['cells']:
        if 'outputs' in cell:
            cell['outputs'] = []
        if 'execution_count' in cell:
            cell['execution_count'] = None


def remove_cell_ids(nb):
    """
    Remove all cell IDs from a notebook in-place.

    Args:
        nb (``nbformat.NotebookNode``): a notebook
    """
    for cell in nb['cells']:
        if 'id' in cell:
            cell.pop('id')


def lock(cell):
    """
    Make a cell non-editable and non-deletable in-place.

    Args:
        cell (``nbformat.NotebookNode``): cell to be locked
    """
    m = cell['metadata']
    m["editable"] = False
    m["deletable"] = False


def add_tag(cell, tag):
    """
    Add a tag to a cell, returning a copy.

    Args:
        cell (``nbformat.NotebookNode``): the cell to add a tag to
        tag (``str``): the tag to add

    Returns:
        ``nbformat.NotebookNode``: a copy of ``cell`` with the tag added
    """
    cell = copy.deepcopy(cell)
    if "tags" not in cell["metadata"]:
        cell["metadata"]["tags"] = []
    cell["metadata"]["tags"].append(tag)
    return cell


def has_tag(cell, tag):
    """
    Determine whether a cell has a tag.

    Args:
        cell (``nbformat.NotebookNode``): the cell to check
        tag (``str``): the tag to check for

    Returns:
        ``nbformat.NotebookNode``: whether ``cell`` is tagged with ``tag``
    """
    return tag in cell["metadata"].get("tags", [])


def remove_tag(cell, tag):
    """
    Remove a tag from a cell, returning a copy.

    Args:
        cell (``nbformat.NotebookNode``): the cell to remove a tag from
        tag (``str``): the tag to remove

    Returns:
        ``nbformat.NotebookNode``: a copy of ``cell`` with the tag removed
    """
    cell = copy.deepcopy(cell)
    if "tags" not in cell["metadata"] or tag not in cell["metadata"]["tags"]:
        return cell
    cell["metadata"]["tags"].remove(tag)
    return cell


def str_to_doctest(code_lines, lines):
    """
    Convert a list of lines of Python code ``code_lines`` to the doctest format and appending the
    results to ``lines``.

    Args:
        code_lines (``list[str]``): the code to convert
        lines (``list[str]``): the list to append the converted lines to

    Returns:
        ``list[str]``: a pointer to ``lines``
    """
    if len(code_lines) == 0:
        return lines
    line = code_lines.pop(0)
    if line.startswith(" ") or line.startswith("\t"):
        return str_to_doctest(code_lines, lines + ["... " + line])
    elif bool(re.match(r"^except[\s\w]*:", line)) or line.startswith("elif ") or \
            line.startswith("else:") or line.startswith("finally:"):
        return str_to_doctest(code_lines, lines + ["... " + line])
    elif len(lines) > 0 and lines[-1].strip().endswith("\\"):
        return str_to_doctest(code_lines, lines + ["... " + line])
    else:
        return str_to_doctest(code_lines, lines + [">>> " + line])


def run_tests(nb_path, debug=False, seed=None, plugin_collection=None):
    """
    Grade a notebook and throw an error if it does not receive a perfect score.

    Args:
        nb_path (``pathlib.Path``): the path to the notebook to grade
        debug (``bool``, optional): whether to raise errors instead of ignoring them
        seed (``int``, optional): an RNG seed for notebook execution
        plugin_collection (``otter.plugins.PluginCollection``, optional): plugins to run while
            grading

    Raises:
        ``RuntimeError``: if the grade received by the notebook is not 100%
    """
    curr_dir = os.getcwd()
    os.chdir(nb_path.parent)

    results = grade_notebook(
        nb_path.name, tests_glob=glob(os.path.join("tests", "*.py")), cwd=os.getcwd(), 
    	test_dir=os.path.join(os.getcwd(), "tests"), ignore_errors = not debug, seed=seed,
        plugin_collection=plugin_collection
    )

    if results.total != results.possible:
        raise RuntimeError(f"Some autograder tests failed in the autograder notebook:\n" + \
            indent(results.summary(), '    '))

    os.chdir(curr_dir)


def write_otter_config_file(assignment):
    """
    Create an Otter configuration file (a ``.otter`` file) for students to use Otter tools,
    including saving environments and submitting to an Otter Service deployment, using assignment
    configurations. Writes the resulting file to the ``autograder`` and ``student`` subdirectories
    of ``assignment.result``.

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment config
    """
    config = {}

    config["notebook"] = assignment.master.name
    config["save_environment"] = assignment.save_environment
    config["ignore_modules"] = assignment.ignore_modules

    if assignment.variables:
        config["variables"] = assignment.variables

    config_name = assignment.master.stem + '.otter'
    with open(assignment.get_ag_path(config_name), "w+") as f:
        json.dump(config, f, indent=4)
    with open(assignment.get_stu_path(config_name), "w+") as f:
        json.dump(config, f, indent=4)


# TODO: update for new assign format
def run_generate_autograder(assignment, gs_username, gs_password, plugin_collection=None):
    """
    Run Otter Generate on the autograder directory to generate a Gradescope zip file. Relies on 
    configurations in ``assignment.generate``.

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
        gs_username (``str``): Gradescope username for token generation
        gs_password (``str``): Gradescope password for token generation
        plugin_collection (``otter.plugins.PluginCollection``, optional): a plugin collection to pass
            to Otter Generate
    """
    curr_dir = os.getcwd()
    os.chdir(str(assignment.get_ag_path()))

    # use temp tests dir
    test_dir = "tests"
    if assignment.is_python and not assignment.tests.files and assignment._temp_test_dir is None:
        raise RuntimeError("Failed to create temp tests directory for Otter Generate")

    elif assignment.is_python and not assignment.tests.files:
        test_dir = str(assignment._temp_test_dir)

    requirements = None
    if assignment.requirements:
        if assignment.is_r:
            requirements = 'requirements.R'
        else:
            requirements = 'requirements.txt'

    files = []
    if assignment.files:
        files += assignment.files

    if assignment.autograder_files:
        ag_dir = os.getcwd()
        os.chdir(curr_dir)
        output_dir = assignment.get_ag_path()

        # copy files
        for file in assignment.autograder_files:

            # if a directory, copy the entire dir
            if os.path.isdir(file):
                shutil.copytree(file, str(output_dir / os.path.basename(file)))

            else:
                # check that file is in subdir
                assert os.getcwd() in os.path.abspath(file), \
                    f"{file} is not in a subdirectory of the master notebook directory"
                file_path = pathlib.Path(file).resolve()
                rel_path = file_path.parent.relative_to(pathlib.Path(os.getcwd()))
                os.makedirs(output_dir / rel_path, exist_ok=True)
                shutil.copy(file, str(output_dir / rel_path))

        os.chdir(ag_dir)

        files += assignment.autograder_files

    otter_config = assignment.get_otter_config()
    if otter_config:
        # TODO: move this filename into a global variable somewhere and remove all of the places
        # it's hardcoded
        with open("otter_config.json", "w+") as f:
            json.dump(otter_config, f, indent=2)

    # TODO: change generate_autograder so that only necessary kwargs are needed
    timestamp = dt.datetime.now().strftime("%Y_%m_%dT%H_%M_%S_%f")
    notebook_name = assignment.master.stem
    output_path = f"{notebook_name}-autograder_{timestamp}.zip"
    generate_autograder(
        tests_dir=test_dir,
        output_path=output_path,
        config="otter_config.json" if otter_config else None,
        lang="python" if assignment.is_python else "r",
        requirements=requirements,
        overwrite_requirements=assignment.overwrite_requirements,
        environment="environment.yml" if assignment.environment else None,
        no_environment=False,
        username=gs_username,
        password=gs_password,
        files=files,
        plugin_collection=plugin_collection,
        assignment=assignment,
        python_version=assignment.get_python_version(),
    )

    # clean up temp tests dir
    if assignment._temp_test_dir is not None:
        shutil.rmtree(str(assignment._temp_test_dir))

    os.chdir(curr_dir)


def add_assignment_name_to_notebook(nb, assignment):
    """
    Add the assignment name from the assignment config to the provided notebook's metadata in-place.

    If ``assignment`` has a name, the name is added to the notebook metadata, as
    ``nb["metadata"]["otter"]["assignment_name"]``.

    Args:
        nb (``nbformat.NotebookNode``): the notebook to add the name to
        assignment (``otter.assign.assignment.Assignment``): the assignment config
    """
    if assignment.name is not None:
        if NOTEBOOK_METADATA_KEY not in nb["metadata"]:
            nb["metadata"][NOTEBOOK_METADATA_KEY] = {}
        nb["metadata"][NOTEBOOK_METADATA_KEY]["assignment_name"] = assignment.name
