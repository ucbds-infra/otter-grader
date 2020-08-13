"""
Utilities for Otter Assign
"""

import re
import os
import json
import pprint
import pathlib

from glob import glob

from .constants import SEED_REGEX, BLOCK_QUOTE

from ..argparser import get_parser
from ..execute import grade_notebook
from ..generate.autograder import main as generate_autograder
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

# def is_seed_cell(cell):
#     """
#     Returns whether ``cell`` is seed cell
    
#     Args:
#         cell (``nbformat.NotebookNode``): notebook cell
    
#     Returns:
#         ``bool``: whether the cell is a seed cell
#     """
#     if cell['cell_type'] != 'code':
#         return False
#     source = get_source(cell)
#     return source and re.match(SEED_REGEX, source[0], flags=re.IGNORECASE)

def is_markdown_cell(cell):
    """
    Returns whether ``cell`` is Markdown cell
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the cell is a Markdown cell
    """
    return cell.cell_type == 'markdown'


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
    elif line.startswith("except:") or line.startswith("elif ") or line.startswith("else:") or line.startswith("finally:"):
        return str_to_doctest(code_lines, lines + ["... " + line])
    elif len(lines) > 0 and lines[-1].strip().endswith("\\"):
        return str_to_doctest(code_lines, lines + ["... " + line])
    else:
        return str_to_doctest(code_lines, lines + [">>> " + line])

def run_tests(nb_path, debug=False, seed=None):
    """
    Runs tests in the autograder version of the notebook
    
    Args:
        nb_path (``pathlib.Path``): path to iPython notebooks
        debug (``bool``, optional): ``True`` if errors should not be ignored
        seed (``int``, optional): random seed for notebook execution
    """
    curr_dir = os.getcwd()
    os.chdir(nb_path.parent)
    # print(os.getcwd())
    results = grade_notebook(
        nb_path.name, glob(os.path.join("tests", "*.py")), cwd=os.getcwd(), 
    	test_dir=os.path.join(os.getcwd(), "tests"), ignore_errors = not debug, seed=seed
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

    service = assignment.service
    if service:
        config.update({
            "endpoint": service["endpoint"],
            "auth": service.get("auth", "google"),
            "assignment_id": service["assignment_id"],
            "class_id": service["class_id"]
        })

    config["notebook"] = service.get('notebook', master.name)
    config["save_environment"] = assignment.save_environment
    config["ignore_modules"] = assignment.ignore_modules

    if assignment.variables:
        config["variables"] = assignment.variables

    config_name = master.stem + '.otter'
    with open(result / 'autograder' / config_name, "w+") as f:
        json.dump(config, f, indent=4)
    with open(result / 'student' / config_name, "w+") as f:
        json.dump(config, f, indent=4)

def run_generate_autograder(result, assignment, args):
    """
    Runs Otter Generate on the autograder directory to generate a Gradescope zip file. Relies on 
    configurations in ``assignment.generate`` and ``args``.

    Args:
        result (``pathlib.Path``): the path to the result directory
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
        args (``argparse.Namespace``): parsed command line arguments
    """
    generate_args = assignment.generate
    if generate_args is True:
        generate_args = {}

    curr_dir = os.getcwd()
    os.chdir(str(result / 'autograder'))
    generate_cmd = ["generate", "autograder"]

    if generate_args.get('points', None) is not None:
        generate_cmd += ["--points", str(generate_args.get('points', None))]
    
    if generate_args.get('threshold', None) is not None:
        generate_cmd += ["--threshold", str(generate_args.get('threshold', None))]
    
    if generate_args.get('show_stdout', False):
        generate_cmd += ["--show-stdout"]
    
    if generate_args.get('show_hidden', False):
        generate_cmd += ["--show-hidden"]
    
    if generate_args.get('grade_from_log', False):
        generate_cmd += ["--grade-from-log"]
    
    if generate_args.get('seed', None) is not None:
        generate_cmd += ["--seed", str(generate_args.get('seed', None))]

    if generate_args.get('public_multiplier', None) is not None:
        generate_cmd += ["--public-multiplier", str(generate_args.get('public_multiplier', None))]

    if generate_args.get('pdfs', {}):
        pdf_args = generate_args.get('pdfs', {})
        token = APIClient.get_token()
        generate_cmd += ["--token", token]
        generate_cmd += ["--course-id", str(pdf_args["course_id"])]
        generate_cmd += ["--assignment-id", str(pdf_args["assignment_id"])]

        if not pdf_args.get("filtering", True):
            generate_cmd += ["--unfiltered-pdfs"]
    
    if assignment.is_r:
        generate_cmd += ["-l", "r"]

    requirements = assignment.requirements or args.requirements
    requirements = get_relpath(result / 'autograder', pathlib.Path(requirements))
    if os.path.isfile(requirements):
        generate_cmd += ["-r", str(requirements)]
        if assignment.overwrite_requirements or args.overwrite_requirements:
            generate_cmd += ["--overwrite-requirements"]
    
    if assignment.files or args.files:
        generate_cmd += assignment.files or args.files

    if assignment.variables:
        generate_cmd += ["--serialized-variables", str(assignment.variables)]
    
    # TODO: change this to import and direct call
    parser = get_parser()
    args = parser.parse_args(generate_cmd)
    generate_autograder(args)

    os.chdir(curr_dir)
