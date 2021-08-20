"""Master notebook transformer for Otter Assign"""

import copy
import nbformat
import os
import pathlib

from .blocks import BlockType, get_cell_config, is_assignment_config_cell, is_block_boundary_cell
from .cell_generators import (
    add_export_tag_to_cell, gen_init_cell, gen_markdown_response_cell, gen_export_cells, 
    gen_check_all_cell
)
from .questions import create_question_config
from .solutions import has_seed, SOLUTION_CELL_TAG
from .tests import any_public_tests
from .utils import add_tag, AssignNotebookFormatException, EmptyCellException, is_cell_type, is_ignore_cell


def transform_notebook(nb, assignment):
    """
    Converts a master notebook to an Otter-formatted solutions notebook, parsing test cells into
    dictionaries ready to be written as OK test files.

    Args:
        nb (``nbformat.NotebookNode``): the master notebook
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations

    Returns:
        ``tuple[nbformat.NotebookNode, dict]``: the transformed notebook and a dictionary mapping 
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

        # TODO: convert export_cell to default dict
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
    notebook. 

    Replaces test cells with a cell calling ``otter.Notebook.check``, inserts Markdown
    response cells for manual questions with Markdown solutions, and comments out question metadata 
    in question cells, among other things.

    Args:
        cells (``list[nbformat.NotebookNode]``): original code cells
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
    
    Returns:
        ``tuple[list, dict]``: list of cleaned notebook cells and a dictionary mapping test names to 
        their parsed contents
    """
    if assignment.is_r:
        from otter.assign.r_adapter.tests import read_test, gen_test_cell
    else:
        from otter.assign.tests import read_test, gen_test_cell

    curr_block = []  # allow nested blocks
    transformed_cells = []
    test_files = {}

    question_metadata, test_cases, has_prompt, no_solution = \
        {}, [], False, False

    solution_has_md_cells, prompt_insertion_index = False, None

    need_begin_export, need_end_export = False, False

    for i, cell in enumerate(cells):

        if is_ignore_cell(cell):
            continue

        # check for assignment config
        if is_assignment_config_cell(cell):
            assignment.update(get_cell_config(cell))
            continue

        # check for an end to the current block
        if len(curr_block) > 0 and is_block_boundary_cell(cell, curr_block[-1], end=True):
            block_type = curr_block.pop()  # remove the block

            if block_type is BlockType.QUESTION:

                if question_metadata["manual"] or question_metadata["export"]:
                    need_end_export = True

                # generate a check cell
                if test_cases:
                    check_cell = gen_test_cell(question_metadata, test_cases, test_files, assignment)

                    # only add to notebook if there's a response cell or if there are public tests
                    # don't add cell if the 'check_cell' key of quetion_metadata is false
                    if (not no_solution or any_public_tests(test_cases)) and \
                            question_metadata["check_cell"]:
                        transformed_cells.append(check_cell)

                # TODO: reformat this state update
                question_metadata, test_cases, has_prompt, no_solution = \
                    {}, [], False, False
                solution_has_md_cells, prompt_insertion_index = False, None

            elif block_type is BlockType.SOLUTION:
                if not has_prompt and solution_has_md_cells:
                    if prompt_insertion_index is None:
                        # TODO: make this error nicer?
                        raise RuntimeError("Could not find prompt insertion index")
                    transformed_cells.insert(prompt_insertion_index, gen_markdown_response_cell())
                    has_prompt = True

            continue  # if this is an end to the last nested block, we're OK

        # check for invalid block ends
        for block_type in BlockType:
            if is_block_boundary_cell(cell, block_type, end=True):

                # if a child is missing an end block cell, raise an error
                if block_type in curr_block:
                    raise AssignNotebookFormatException(
                        f"Found an end { block_type.value } cell with an un-ended child " + \
                            f"{ curr_block[-1].value } block", i)

                # otherwise raise an error for an end with no begin
                else:
                    raise AssignNotebookFormatException(
                        f"Found an end { block_type.value } cell with no begin block cell", i)

        # check for begin blocks
        found_begin = False
        for block_type in BlockType:
            if is_block_boundary_cell(cell, block_type):
                found_begin = True
                break

        if found_begin:
            if len(curr_block) == 0 and block_type is not BlockType.QUESTION:
                raise AssignNotebookFormatException(
                    f"Found a begin { block_type.value } cell outside a question", i)
            elif len(curr_block) > 0 and block_type is BlockType.QUESTION:
                raise AssignNotebookFormatException(
                    f"Found a begin { block_type.value } cell inside another question", i)
            elif len(curr_block) > 1:
                raise AssignNotebookFormatException(
                    f"Found a begin { block_type.value } cell inside a { curr_block[-1].value } " + \
                        f"block", i)
            elif block_type is BlockType.PROMPT and has_prompt:  # has_prompt was set by the solution block
                raise AssignNotebookFormatException("Found a prompt block after a solution block", i)

            # if not an invalid begin cell, update state
            if block_type is BlockType.PROMPT:
                has_prompt = True

            elif block_type is BlockType.SOLUTION and not has_prompt:
                prompt_insertion_index = len(transformed_cells)

            elif block_type is BlockType.TESTS and not has_prompt:
                no_solution = True

            elif block_type is BlockType.QUESTION:
                question_metadata = create_question_config(get_cell_config(cell))
                if question_metadata["manual"] or question_metadata["export"]:
                    need_begin_export = True

            curr_block.append(block_type)
            continue

        # if in a block, process the current cell
        if len(curr_block) > 0:
            if curr_block[-1] == BlockType.TESTS:
                if not is_cell_type(cell, "code"):
                    raise AssignNotebookFormatException("Found a non-code cell in tests block", i)
                test_case = read_test(cell, question_metadata, assignment)
                test_cases.append(test_case)
                continue

            elif curr_block[-1] == BlockType.SOLUTION:
                cell = add_tag(cell, SOLUTION_CELL_TAG)

                if is_cell_type(cell, "markdown"):
                    solution_has_md_cells = True

        # add export tags if needed
        export_delim_cell = None
        if need_begin_export:
            if is_cell_type(cell, "markdown"):
                cell = add_export_tag_to_cell(cell)
            else:
                export_delim_cell = nbformat.v4.new_markdown_cell()
                export_delim_cell = add_export_tag_to_cell(export_delim_cell)
            need_begin_export = False
        if need_end_export:
            if is_cell_type(cell, "markdown"):
                cell = add_export_tag_to_cell(cell, end=True)
            else:
                if export_delim_cell is None:
                    export_delim_cell = nbformat.v4.new_markdown_cell()
                export_delim_cell = add_export_tag_to_cell(export_delim_cell, end=True)
            need_end_export = False

        if export_delim_cell is not None:
            transformed_cells.append(export_delim_cell)

        if has_seed(cell):
            assignment.seed_required = True

        # this is just a normal cell so add it to transformed_cells
        transformed_cells.append(cell)

    return transformed_cells, test_files
