"""Utilities for Otter Assign"""

import copy
import datetime as dt
import json
import nbformat as nbf
import os
import pathlib
import re
import shutil

from contextlib import contextmanager
from glob import glob
from textwrap import indent

from .constants import SEED_REGEX, BLOCK_QUOTE, IGNORE_REGEX

from ..execute import grade_notebook
from ..generate import main as generate_autograder
from ..generate.token import APIClient
from ..utils import get_relpath, get_source


class EmptyCellException(Exception):
    """
    Exception for empty cells to indicate deletion
    """


class AssignNotebookFormatException(Exception):
    """
    """
    def __init__(self, message, question_metadata, cell_index, *args, **kwargs):
        question_name = question_metadata.get("name")
        message += " ("
        if question_name is not None:
            message += f"question { question_name }, "
        message = message + f"cell number { cell_index + 1 })"
        super().__init__(message, *args, **kwargs)


#---------------------------------------------------------------------------------------------------
# Getters
#---------------------------------------------------------------------------------------------------

# TODO: remove
def get_spec(source, begin):
    """
    Returns the line number of the spec begin line or ``None``. Converts ``begin`` to an uppercase 
    string and looks for a line matching ``f"BEGIN {begin.upper()}"``. Used for finding question and
    assignment metadata, which match ``BEGIN QUESTION`` and ``BEGIN ASSIGNMENT``, resp.
    
    Args:
        source (``list`` of ``str``): cell source as a list of lines of text
        begin (``str``): the spec to look for
    
    Returns:
        ``int``: line number of BEGIN ASSIGNMENT, if present
        ``None``: if BEGIN ASSIGNMENT not present in the cell
    """
    block_quotes = [
        i for i, line in enumerate(source) if line[:3] == BLOCK_QUOTE
    ]
    assert len(block_quotes) % 2 == 0, f"wrong number of block quote delimieters in {source}"

    begins = [
        block_quotes[i] + 1 for i in range(0, len(block_quotes), 2) 
        if source[block_quotes[i]+1].strip(' ') == f"BEGIN {begin.upper()}"
    ]
    assert len(begins) <= 1, f'multiple BEGIN {begin.upper()} blocks defined in {source}'
    
    return begins[0] if begins else None

def get_notebook_language(nb):
    """
    Parse the notebook kernel language and return it as a string.

    Args:
        nb (``nbformat.NotebookNode``): the notebook

    Returns:
        ``str``: the name of the language as a lowercased string
    """
    return nb["metadata"]["kernelspec"]["language"].lower()


#---------------------------------------------------------------------------------------------------
# Cell Type Checkers
#---------------------------------------------------------------------------------------------------

def is_ignore_cell(cell):
    """
    Returns whether the current cell should be ignored
    
    Args:
        cell (``nbformat.NotebookNode``): a notebook cell

    Returns:
        ``bool``: whether the cell is a ignored
    """
    source = get_source(cell)
    return source and re.match(IGNORE_REGEX, source[0], flags=re.IGNORECASE)

def is_cell_type(cell, cell_type):
    return cell["cell_type"] == cell_type


#---------------------------------------------------------------------------------------------------
# Cell Reformatters
#---------------------------------------------------------------------------------------------------

def remove_output(nb):
    """
    Removes all outputs from a notebook in-place
    
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
    Removes all cell IDs from a notebook in-place
    
    Args:
        nb (``nbformat.NotebookNode``): a notebook
    """
    for cell in nb['cells']:
        if 'id' in cell:
            cell.pop('id')

def lock(cell):
    """
    Makes a cell non-editable and non-deletable in-place

    Args:
        cell (``nbformat.NotebookNode``): cell to be locked
    """
    m = cell['metadata']
    m["editable"] = False
    m["deletable"] = False

def add_tag(cell, tag):
    """
    """
    cell = copy.deepcopy(cell)
    if "tags" not in cell["metadata"]:
        cell["metadata"]["tags"] = []
    cell["metadata"]["tags"].append(tag)
    return cell

def has_tag(cell, tag):
    """
    """
    return tag in cell["metadata"].get("tags", [])

def remove_tag(cell, tag):
    """
    """
    cell = copy.deepcopy(cell)
    if "tags" not in cell["metadata"] or tag not in cell["metadata"]["tags"]:
        return cell
    cell["metadata"]["tags"].remove(tag)
    return cell


#---------------------------------------------------------------------------------------------------
# Miscellaneous
#---------------------------------------------------------------------------------------------------

def str_to_doctest(code_lines, lines):
    """
    Converts a list of lines of Python code ``code_lines`` to a list of doctest-formatted lines ``lines``

    Args:
        code_lines (``list``): list of lines of python code
        lines (``list``): set of characters used to create function name
    
    Returns:
        ``list`` of ``str``: doctest formatted list of lines
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
    Runs tests in the autograder version of the notebook
    
    Args:
        nb_path (``pathlib.Path``): path to iPython notebooks
        debug (``bool``, optional): ``True`` if errors should not be ignored
        seed (``int``, optional): random seed for notebook execution
        plugin_collection(``otter.plugins.PluginCollection``, optional): plugins to run with tests
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

def write_otter_config_file(master, result, assignment):
    """
    Creates an Otter configuration file (a ``.otter`` file) for students to use Otter tools, including
    saving environments and submitting to an Otter Service deployment, using assignment configurations.
    Writes the resulting file to the ``autograder`` and ``student`` subdirectories of ``result``.

    Args:
        master (``pathlib.Path``): path to master notebook
        result (``pathlib.Path``): path to result directory
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
    """
    config = {}

    config["notebook"] = master.name
    config["save_environment"] = assignment.save_environment
    config["ignore_modules"] = assignment.ignore_modules

    if assignment.variables:
        config["variables"] = assignment.variables

    config_name = master.stem + '.otter'
    with open(result / 'autograder' / config_name, "w+") as f:
        json.dump(config, f, indent=4)
    with open(result / 'student' / config_name, "w+") as f:
        json.dump(config, f, indent=4)

# TODO: update for new assign format
def run_generate_autograder(result, assignment, gs_username, gs_password, plugin_collection=None):
    """
    Runs Otter Generate on the autograder directory to generate a Gradescope zip file. Relies on 
    configurations in ``assignment.generate``.

    Args:
        result (``pathlib.Path``): the path to the result directory
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
        gs_username (``str``): Gradescope username for token generation
        gs_password (``str``): Gradescope password for token generation
        plugin_collection (``otter.plugins.PluginCollection``, optional): a plugin collection to pass
            to Otter Generate
    """
    generate_args = assignment.generate
    if generate_args is True:
        generate_args = {}

    if "pdfs" in generate_args:
        raise ValueError("The 'pdfs' key of 'generate' is no longer supported. Put any " + \
                         "'pdfs' configurations inside the 'generate' key itself.")

    if assignment.is_r:
        generate_args["lang"] = "r"

    curr_dir = os.getcwd()
    os.chdir(str(result / 'autograder'))

    # use temp tests dir
    test_dir = "tests"
    if assignment.is_python and not assignment.tests["files"] and assignment._temp_test_dir is None:
        raise RuntimeError("Failed to create temp tests directory for Otter Generate")

    elif assignment.is_python and not assignment.tests["files"]:
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
        output_dir  = result / 'autograder'

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

    # TODO: move this config out of the assignment metadata and into the generate key
    if assignment.variables:
        generate_args['serialized_variables'] = str(assignment.variables)

    if generate_args:
        with open("otter_config.json", "w+") as f:
            json.dump(generate_args, f, indent=2)

    # TODO: change generate_autograder so that only necessary kwargs are needed
    timestamp = dt.datetime.now().strftime("%Y_%m_%dT%H_%M_%S_%f")
    notebook_name = assignment.master.stem
    output_path = f"{notebook_name}-autograder_{timestamp}.zip"
    generate_autograder(
        tests_dir=test_dir,
        output_path=output_path,
        config="otter_config.json" if generate_args else None,
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
    )

    # clean up temp tests dir
    if assignment._temp_test_dir is not None:
        shutil.rmtree(str(assignment._temp_test_dir))

    os.chdir(curr_dir)

@contextmanager
def patch_copytree():
    """
    A context manager patch for ``shutil.copytree` on WSL. Shamelessly stolen from
    https://bugs.python.org/issue38633 (see for more information)
    """
    import errno, shutil
    orig_copyxattr = shutil._copyxattr
    
    def patched_copyxattr(src, dst, *, follow_symlinks=True):
        try:
            orig_copyxattr(src, dst, follow_symlinks=follow_symlinks)
        except OSError as ex:
            if ex.errno != errno.EACCES: raise
    
    shutil._copyxattr = patched_copyxattr

    yield

    shutil._copyxattr = orig_copyxattr


def cell_from_source(cell_type, source_lines):
    """
    """
    return getattr(nbf.v4, f"new_{cell_type}_cell")("\n".join(source_lines))
