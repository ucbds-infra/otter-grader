import os
import pathlib
import nbformat

from .assignment import is_assignment_cell, read_assignment_metadata
from .cell_generators import (
    gen_init_cell, gen_markdown_response_cell, gen_export_cells, gen_check_all_cell, 
    gen_close_export_cell, add_close_export_to_cell
)
from .questions import is_question_cell, read_question_metadata, gen_question_cell
from .solutions import is_solution_cell, is_markdown_solution_cell
from .tests import is_test_cell, read_test, gen_test_cell
from .utils import is_seed_cell, EmptyCellException

def transform_notebook(nb, assignment, args):
    """Converts a master notebook to an Otter-formatted solutions notebook and tests directory

    Args:
        nb_path (``pathlib.Path``): path to master notebook
        dir (``pathlib.Path``): output directory
        args (``argparse.Namespace``): parsed command line arguments

    Returns:
        ``str``: path to the solutions notebook

    """
    transformed_cells, test_files = get_transformed_cells(nb['cells'], assignment)

    if assignment.init_cell and not args.no_init_cell:
        transformed_cells = [gen_init_cell()] + transformed_cells

    if assignment.check_all_cell and not args.no_check_all:
        transformed_cells += gen_check_all_cell()
    
    if assignment.export_cell and not args.no_export_cell:
        export_cell = assignment.export_cell
        if export_cell is True:
            export_cell = {}

        transformed_cells += gen_export_cells(
            export_cell.get('instructions', ''), 
            pdf = export_cell.get('pdf', True),
            filtering = export_cell.get('filtering', True)
        )

    transformed_nb = nbformat.v4.new_notebook()
    transformed_nb['cells'] = transformed_cells

    return transformed_nb, test_files

def get_transformed_cells(cells, assignment):
    """Generate notebook cells for the Otter version of a master notebook

    Args:
        cells (``list`` of ``nbformat.NotebookNode``): original code cells
        tests_dir (``str``): path to directory of tests
    
    Returns:
        ``list`` of ``nbformat.NotebookNode``: cleaned notebook cells
    """
    # global SEED_REQUIRED, ASSIGNMENT_METADATA
    transformed_cells, test_files = [], {}
    question_metadata, test_cases, processed_solution, md_has_prompt = {}, [], False, False
    need_close_export, no_solution = False, False

    for cell in cells:

        # this is the prompt cell or if a manual question then the solution cell
        if question_metadata and not processed_solution:
            assert not is_question_cell(cell), f"Found question cell before end of previous question cell: {cell}"

            # if this isn't a MD solution cell but in a manual question, it has a prompt
            if not is_markdown_solution_cell(cell) and question_metadata.get('manual', False):
                md_has_prompt = True
            
            # if there is no prompt, add a prompt cell
            elif is_markdown_solution_cell(cell) and not md_has_prompt:
                transformed_cells.append(gen_markdown_response_cell())

            # if this is a test cell, this question has no response cell for the students, so we don't
            # include it in the output notebook but we need a test file
            elif is_test_cell(cell):
                no_solution = True
                gen_test_cell(question_metadata, test_cases, test_files)

            elif is_seed_cell(cell):
                assignment.seed_required = True
                continue

            if not no_solution:
                transformed_cells.append(cell)
            
            processed_solution = True

        # if this is a test cell, parse and add to test_cases
        elif question_metadata and processed_solution and is_test_cell(cell):
            test = read_test(cell)
            test_cases.append(test)

        # # if this is a solution cell, append. if manual question and no prompt, also append prompt cell
        # elif question_metadata and processed_solution and is_solution_cell(cell):
        #     if is_markdown_solution_cell(cell) and not md_has_prompt:
        #         transformed_cells.append(gen_markdown_response_cell())
        #     transformed_cells.append(cell)

        else:
            # the question is over -- we've seen the question and solution and any tests
            if question_metadata and processed_solution:

                # create a Notebook.check cell
                if test_cases:
                    check_cell = gen_test_cell(question_metadata, test_cases, test_files)

                    # only add to notebook if there's a response cell
                    if not no_solution:
                        transformed_cells.append(check_cell)

                # add a cell with <!-- END QUESTION --> if a manually graded question
                manual = question_metadata.get('manual', False)
                if manual:
                    need_close_export = True
                
                # reset vars
                question_metadata, processed_solution, test_cases, md_has_prompt, no_solution = {}, False, [], False, False

            # update assignment config if present; don't add cell to output nb
            elif is_assignment_cell(cell):
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
        check_cell = gen_test_cell(question_metadata, test_cases, test_files)
        if not no_solution:
            transformed_cells.append(check_cell)

    return transformed_cells, test_files
