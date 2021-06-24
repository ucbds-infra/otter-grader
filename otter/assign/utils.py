"""
Utilities for Otter Assign
"""

import re
import os
import json
import pprint
import pathlib
import shutil

from glob import glob
from contextlib import contextmanager

from .constants import SEED_REGEX, BLOCK_QUOTE, IGNORE_REGEX

from ..argparser import get_parser
from ..execute import grade_notebook
from ..generate import main as generate_autograder
from ..generate.token import APIClient
from ..utils import get_relpath, get_source

class EmptyCellException(Exception):
    """
    Exception for empty cells to indicate deletion
    """


#---------------------------------------------------------------------------------------------------
# Getters
#---------------------------------------------------------------------------------------------------

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


#---------------------------------------------------------------------------------------------------
# Cell Type Checkers
#---------------------------------------------------------------------------------------------------

def is_markdown_cell(cell):
    """
    Returns whether ``cell`` is Markdown cell
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the cell is a Markdown cell
    """
    return cell.cell_type == 'markdown'

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

def lock(cell):
    """
    Makes a cell non-editable and non-deletable in-place

    Args:
        cell (``nbformat.NotebookNode``): cell to be locked
    """
    m = cell['metadata']
    m["editable"] = False
    m["deletable"] = False


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
    # print(os.getcwd())
    results = grade_notebook(
        nb_path.name, glob(os.path.join("tests", "*.py")), cwd=os.getcwd(), 
    	test_dir=os.path.join(os.getcwd(), "tests"), ignore_errors = not debug, seed=seed,
        plugin_collection=plugin_collection
    )
    assert results.total == results.possible, "Some autograder tests failed:\n\n" + pprint.pformat(results, indent=2)
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

    curr_dir = os.getcwd()
    os.chdir(str(result / 'autograder'))
    generate_cmd = ["generate"]

    if generate_args.get('pdfs', {}):
        pdf_args = generate_args.pop('pdfs', {})
        # token = APIClient.get_token()
        # generate_args['token'] = token
        generate_args['course_id'] = str(pdf_args['course_id'])
        generate_args['assignment_id'] = str(pdf_args['assignment_id'])

        if not pdf_args.get("filtering", True):
            generate_args['filtering'] = False

        if not pdf_args.get('pagebreaks', True):
            generate_args['pagebreaks'] = False

    # use temp tests dir
    if assignment.is_python and not assignment.test_files and assignment._temp_test_dir is None:
        raise RuntimeError("Failed to create temp tests directory for Otter Generate")
    elif assignment.is_python and not assignment.test_files:
        generate_cmd += ["-t", str(assignment._temp_test_dir)]
    
    if assignment.is_r:
        generate_cmd += ["-l", "r"]
        generate_args['lang'] = 'r'

    if assignment.requirements:
        if assignment.is_r:
            requirements = 'requirements.R'
        else:
            requirements = 'requirements.txt'
        generate_cmd += ["-r", str(requirements)]
        if assignment.overwrite_requirements:
            generate_cmd += ["--overwrite-requirements"]

    if assignment.environment:
        environment = 'environment.yml'
        generate_cmd += ["-e", str(environment)]
    
    if gs_username is not None and gs_password is not None:
        generate_cmd += ["--username", gs_username, "--password", gs_password]
    
    if assignment.files:
        generate_cmd += assignment.files

    if assignment.autograder_files:
        ag_files = []
        res = (result / "autograder").resolve()
        for agf in assignment.autograder_files:
            fp = pathlib.Path(agf).resolve()
            rp = get_relpath(res, fp)
            ag_files.append(str(rp))
        generate_cmd += ag_files

    if assignment.variables:
        generate_args['serialized_variables'] = str(assignment.variables)

    if generate_args:
        with open("otter_config.json", "w+") as f:
            json.dump(generate_args, f, indent=2)
    
    # TODO: change this to import and direct call
    parser = get_parser()
    args = parser.parse_args(generate_cmd)
    generate_autograder(**vars(args), assignment=assignment, plugin_collection=plugin_collection)

    # clean up temp tests dir
    if assignment._temp_test_dir is not None:
        shutil.rmtree(str(assignment._temp_test_dir))

    os.chdir(curr_dir)

@contextmanager
def patch_copytree():
    """
    A context manager patch for ``shutil.copytree` on WSL. Shamelessly stolen from https://bugs.python.org/issue38633
    (see for more information)
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
