"""
Master notebook parser and transformer for Otter Assign
"""

import os
import copy
import pathlib
import nbformat

from .assignment import is_assignment_cell, read_assignment_metadata
from .cell_generators import (
    gen_init_cell, gen_markdown_response_cell, gen_export_cells, gen_check_all_cell, 
    gen_close_export_cell, add_close_export_to_cell
)
from .questions import is_question_cell, read_question_metadata, gen_question_cell
from .solutions import is_markdown_solution_cell, has_seed
from .tests import is_test_cell, any_public_tests
from .utils import is_ignore_cell, is_markdown_cell, EmptyCellException

def transform_notebook(nb, assignment):
    """
    Converts a master notebook to an Otter-formatted solutions notebook, parsing test cells into
    dictionaries ready to be written as OK test files.

    Args:
        nb (``nbformat.NotebookNode``): the master notebook
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations

    Returns:
        ``tuple(nbformat.NotebookNode, dict)``: the transformed notebook and a dictionary mapping 
            test names to their parsed contents

    """
    transformed_cells, test_files = get_transformed_cells(nb['cells'], assignment)

    if assignment.init_cell and assignment.is_python:
        transformed_cells = [gen_init_cell(assignment.master.name, assignment.colab)] + transformed_cells

    if assignment.check_all_cell and assignment.is_python:
        transformed_cells += gen_check_all_cell()
    
    if assignment.export_cell and assignment.is_python:
        export_cell = assignment.export_cell
        if export_cell is True:
            export_cell = {}

        transformed_cells += gen_export_cells(
            export_cell.get('instructions', ''), 
            pdf = export_cell.get('pdf', True),
            filtering = export_cell.get('filtering', True),
            force_save = export_cell.get('force_save', False),
            run_tests = export_cell.get('run_tests', False)
        )

    transformed_nb = copy.deepcopy(nb)
    transformed_nb['cells'] = transformed_cells

    return transformed_nb, test_files

def get_transformed_cells(cells, assignment):
    """
    Takes in a list of cells from the master notebook and returns a list of cells for the solutions
    notebook. Replaces test cells with a cell calling ``otter.Notebook.check``, inserts Markdown
    response cells for manual questions with Markdown solutions, and comments out question metadata 
    in question cells, among other things.

    Args:
        cells (``list`` of ``nbformat.NotebookNode``): original code cells
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
    
    Returns:
        ``tuple(list, dict)``: list of cleaned notebook cells and a dictionary mapping test names to 
            their parsed contents
    """
    if assignment.is_r:
        from .r_adapter.tests import read_test, gen_test_cell
    else:
        from .tests import read_test, gen_test_cell
    
    # global SEED_REQUIRED, ASSIGNMENT_METADATA
    transformed_cells, test_files = [], {}
    question_metadata, test_cases, processed_solution, md_has_prompt = {}, [], False, False
    need_close_export, no_solution = False, False
    DEFAULT_SUCCESS_MESSAGE = "Test case passed!" # move
    DEFAULT_FAILURE_MESSAGE = "Test case failed." # move
    for cell in cells:

        if has_seed(cell):
            assignment.seed_required = True            

        if is_ignore_cell(cell):
            continue
        
        # this is the prompt cell or if a manual question then the solution cell
        if question_metadata and not processed_solution:
            assert not is_question_cell(cell), f"Found question cell before end of previous question cell: {cell}"

            # if this isn't a MD solution cell but in a manual question, it has a Markdown prompt
            if question_metadata.get('manual', False) and is_markdown_cell(cell) and not is_markdown_solution_cell(cell):
                md_has_prompt = True
                transformed_cells.append(cell)
                continue
            
            # if this a manual question but not MD solution, it has a code solution cell
            elif question_metadata.get('manual', False) and not is_markdown_solution_cell(cell):
                md_has_prompt = True
            
            # if there is no prompt, add a prompt cell
            elif is_markdown_solution_cell(cell) and not md_has_prompt:
                transformed_cells.append(gen_markdown_response_cell())

            # if this is a test cell, this question has no response cell for the students, so we don't
            # include it in the output notebook but we need a test file
            elif is_test_cell(cell):
                no_solution = True
                test = read_test(cell, question_metadata, assignment)
                test_cases.append(test)

            if not no_solution:
                transformed_cells.append(cell)
            
            processed_solution = True

        # if this is a test cell, parse and add to test_cases
        elif question_metadata and processed_solution and is_test_cell(cell):
            test = read_test(cell, question_metadata, assignment)
            test_cases.append(test)

        else:
            # the question is over -- we've seen the question and solution and any tests and now we 
            # need to get ready to process the next question which *could be this cell*
            if question_metadata and processed_solution:

                # create a Notebook.check cell
                if test_cases:
                    check_cell = gen_test_cell(question_metadata, test_cases, test_files, assignment)

                    # only add to notebook if there's a response cell or if there are public tests
                    # don't add cell if the 'check_cell' key of quetion_metadata is false
                    if (not no_solution or any_public_tests(test_cases)) and \
                            question_metadata.get('check_cell', True):
                        transformed_cells.append(check_cell)

                # add a cell with <!-- END QUESTION --> if a manually graded question
                manual = question_metadata.get('manual', False)
                if manual:
                    need_close_export = True
                
                # reset vars
                question_metadata, processed_solution, test_cases, md_has_prompt, no_solution = {}, False, [], False, False

            # update assignment config if present; don't add cell to output nb
            if is_assignment_cell(cell):
                assignment.update(read_assignment_metadata(cell))

            # if a question cell, parse metadata, comment out question metadata, and append to nb
            elif is_question_cell(cell):
                question_metadata = read_question_metadata(cell)
                manual = question_metadata.get('manual', False)

                try:
                    transformed_cells.append(gen_question_cell(cell, manual, need_close_export))
                    need_close_export = False
                except EmptyCellException:
                    pass

            elif is_markdown_solution_cell(cell):
                transformed_cells.append(gen_markdown_response_cell())
                transformed_cells.append(cell)

            else:
                assert not is_test_cell(cell), f"Test outside of a question: {cell}"

                if need_close_export:
                    if cell['cell_type'] == 'code':
                        transformed_cells.append(gen_close_export_cell())
                    else:
                        cell = add_close_export_to_cell(cell)
                    need_close_export = False

                transformed_cells.append(cell)

    if test_cases:
        check_cell = gen_test_cell(question_metadata, test_cases, test_files, assignment)
        if not no_solution or any_public_tests(test_cases):
            transformed_cells.append(check_cell)

    return transformed_cells, test_files
