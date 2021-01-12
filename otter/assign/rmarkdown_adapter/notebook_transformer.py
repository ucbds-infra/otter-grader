"""
Rmarkdown adapter for Otter Assign
"""

import os
import copy
import pathlib
import nbformat

from .solutions import is_markdown_solution_cell
from .tests import gen_test_cell, is_test_cell
from .utils import rmd_to_cells, Cell, collapse_empty_cells

from ..assignment import is_assignment_cell, read_assignment_metadata
from ..questions import is_question_cell, read_question_metadata, gen_question_cell
from ..r_adapter.tests import read_test
from ..solutions import has_seed
from ..tests import any_public_tests
from ..utils import is_ignore_cell, is_markdown_cell, EmptyCellException

def transform_notebook(rmd_string, assignment):
    """
    Converts a master RMd file to an Ottr-formatted solutions Rmd file, parsing test cells into
    dictionaries ready to be written as test files.

    Args:
        rmd_string (``str``): the Rmd document as a string
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations

    Returns:
        ``tuple[str, dict]``: the transformed Rmd file and a dictionary mapping test names to their 
            parsed contents

    """
    cells = rmd_to_cells(rmd_string)
    transformed_cells, test_files = get_transformed_cells(cells, assignment)
    collapse_empty_cells(transformed_cells)

    transformed_rmd_string = "\n".join([cell.source for cell in transformed_cells])

    return transformed_rmd_string, test_files

def get_transformed_cells(cells, assignment):
    """
    Takes in a list of cells from the master notebook and returns a list of cells for the solutions
    notebook. Replaces test cells with a cell calling ``ottr::check``, inserts Markdown response cells 
    for manual questions with Markdown solutions, and removes question metadata in question cells, 
    among other things.

    Args:
        cells (``list`` of ``otter.assign.rmarkdown_adapter.utils.Cell``): original code cells
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
    
    Returns:
        ``tuple[list, dict]``: list of cleaned notebook cells and a dictionary mapping test names to 
            their parsed contents
    """
    transformed_cells, test_files = [], {}
    question_metadata, test_cases, processed_solution, md_has_prompt = {}, [], False, False
    need_close_export, no_solution, in_collapse_block = False, False, False

    for cell in cells:

        if not cell.source.strip():
            transformed_cells.append(cell)
            continue

        if has_seed(cell):
            assignment.seed_required = True            

        if is_ignore_cell(cell):
            continue

        # this is the prompt cell or if a manual question then the solution cell
        if question_metadata and not processed_solution:
            assert not is_question_cell(cell), f"Found question cell before end of previous question cell: {cell}"

            if is_test_cell(cell):
                no_solution = True
                test = read_test(cell, question_metadata, assignment, rmd=True)
                test_cases.append(test)

            if not no_solution:
                transformed_cells.append(cell)
            
            processed_solution = True

        # if this is a test cell, parse and add to test_cases
        elif question_metadata and processed_solution and is_test_cell(cell):
            test = read_test(cell, question_metadata, assignment, rmd=True)
            test_cases.append(test)

        else:
            # the question is over -- we've seen the question and solution and any tests and now we 
            # need to get ready to process the next question which *could be this cell*
            if question_metadata and processed_solution:

                # create a Notebook.check cell
                if test_cases:
                    check_cell = gen_test_cell(question_metadata, test_cases, test_files, assignment)

                    # only add to notebook if there's a response cell or if there are public tests
                    if not no_solution or any_public_tests(test_cases):
                        transformed_cells.append(check_cell)
                
                # reset vars
                question_metadata, processed_solution, test_cases, md_has_prompt, no_solution = {}, False, [], False, False

            # update assignment config if present; don't add cell to output nb
            if is_assignment_cell(cell):
                assignment.update(read_assignment_metadata(cell))

            # if a question cell, parse metadata, comment out question metadata, and append to nb
            elif is_question_cell(cell):
                question_metadata = read_question_metadata(cell)
                manual = question_metadata.get('manual', False)

            elif is_markdown_solution_cell(cell):
                # transformed_cells.append(gen_markdown_response_cell())
                transformed_cells.append(cell)

            else:
                assert not is_test_cell(cell), f"Test outside of a question: {cell}"

                transformed_cells.append(cell)

    if test_cases:
        check_cell = gen_test_cell(question_metadata, test_cases, test_files, assignment)
        if not no_solution or any_public_tests(test_cases):
            transformed_cells.append(check_cell)

    return transformed_cells, test_files
