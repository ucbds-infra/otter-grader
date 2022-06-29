"""Master notebook transformer for Otter Assign"""

import copy
import nbformat

from .blocks import BlockType, get_cell_config, is_assignment_config_cell, is_block_boundary_cell
from .cell_factory import CellFactory
from .feature_toggle import FeatureToggle
from .questions import add_point_value_info_to_cell, create_question_config
from .r_adapter.cell_factory import RCellFactory
from .solutions import has_seed, SOLUTION_CELL_TAG
from .tests import any_public_tests, determine_question_point_value
from .utils import add_tag, add_uuid_to_notebook, AssignNotebookFormatException, get_source, \
    is_cell_type, is_ignore_cell


def add_export_tag_to_cell(cell, assignment, end=False):
    """
    Adds an HTML comment to open or close question export for PDF filtering to the top of ``cell``.
    ``cell`` should be a Markdown cell.
    
    Args:
        cell (``nbformat.NotebookNode``): the cell to add the close export to
        assignment (``otter.assign.assignment.Assignment``): the assignment config

    Returns:
        ``nbformat.NotebookNode``: the cell with the close export comment at the top
    """
    if not FeatureToggle.PDF_FILTERING_COMMENTS.value.is_enabled(assignment):
        return cell

    cell = copy.deepcopy(cell)
    source = get_source(cell)
    tag = "<!-- " + ("END" if end else "BEGIN") + " QUESTION -->"
    source = [tag, ""] + source
    cell['source'] = "\n".join(source)
    return cell


def create_cell_factory(assignment):
    """
    Create a ``CellFactory`` for the provided assignment based on the language of the assignment.

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment config

    Returns:
        ``otter.assign.cell_factory.CellFactory``: an instantiated cell factory
    """
    CellFactoryClass = RCellFactory if assignment.is_r else CellFactory
    return CellFactoryClass(assignment)


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

    cell_factory = create_cell_factory(assignment)

    if assignment.init_cell:
        transformed_cells = cell_factory.create_init_cells() + transformed_cells

    if assignment.check_all_cell:
        transformed_cells += cell_factory.create_check_all_cells()

    if assignment.export_cell:
        export_cell = assignment.export_cell
        if export_cell is True:
            export_cell = {}

        # TODO: convert export_cell to default dict
        transformed_cells += cell_factory.create_export_cells()

    transformed_nb = copy.deepcopy(nb)
    transformed_nb['cells'] = transformed_cells
    add_uuid_to_notebook(transformed_nb, assignment)

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

    question_metadata, test_cases, has_prompt, no_solution, last_question_md_cell = \
        {}, [], False, False, None

    solution_has_md_cells, prompt_insertion_index = False, None

    need_begin_export, need_end_export = False, False

    for i, cell in enumerate(cells):

        if is_ignore_cell(cell):
            continue

        # check for assignment config
        if is_assignment_config_cell(cell):
            assignment.update_(get_cell_config(cell))
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

                # add points to question cell if specified
                if assignment.show_question_points and last_question_md_cell is not None:
                    points = determine_question_point_value(question_metadata, test_cases)
                    transformed_cells[last_question_md_cell] = \
                        add_point_value_info_to_cell(transformed_cells[last_question_md_cell], points)

                # TODO: reformat this state update
                question_metadata, test_cases, has_prompt, no_solution, last_question_md_cell = \
                    {}, [], False, False, None
                solution_has_md_cells, prompt_insertion_index = False, None

            elif block_type is BlockType.SOLUTION:
                if not has_prompt and solution_has_md_cells:
                    if prompt_insertion_index is None:
                        # TODO: make this error nicer?
                        raise RuntimeError("Could not find prompt insertion index")
                    transformed_cells.insert(
                        prompt_insertion_index, CellFactory.create_markdown_response_cell())
                    has_prompt = True

            continue  # if this is an end to the last nested block, we're OK

        # check for invalid block ends
        for block_type in BlockType:
            if is_block_boundary_cell(cell, block_type, end=True):

                # if a child is missing an end block cell, raise an error
                if block_type in curr_block:
                    raise AssignNotebookFormatException(
                        f"Found an end { block_type.value } cell with an un-ended child " + \
                            f"{ curr_block[-1].value } block", question_metadata, i)

                # otherwise raise an error for an end with no begin
                else:
                    raise AssignNotebookFormatException(
                        f"Found an end { block_type.value } cell with no begin block cell",
                        question_metadata, i)

        # check for begin blocks
        found_begin = False
        for block_type in BlockType:
            if is_block_boundary_cell(cell, block_type):
                found_begin = True
                break

        if found_begin:
            if len(curr_block) == 0 and block_type is not BlockType.QUESTION:
                raise AssignNotebookFormatException(
                    f"Found a begin { block_type.value } cell outside a question", 
                    question_metadata, i)
            elif len(curr_block) > 0 and block_type is BlockType.QUESTION:
                raise AssignNotebookFormatException(
                    f"Found a begin { block_type.value } cell inside another question", 
                    question_metadata, i)
            elif len(curr_block) > 1:
                raise AssignNotebookFormatException(
                    f"Found a begin { block_type.value } cell inside a { curr_block[-1].value } " + \
                        f"block", question_metadata, i)
            elif block_type is BlockType.PROMPT and has_prompt:  # has_prompt was set by the solution block
                raise AssignNotebookFormatException(
                    "Found a prompt block after a solution block", question_metadata, i)

            # if not an invalid begin cell, update state
            if block_type is BlockType.PROMPT:
                has_prompt = True

            elif block_type is BlockType.SOLUTION and not has_prompt:
                prompt_insertion_index = len(transformed_cells)

            elif block_type is BlockType.TESTS and not has_prompt:
                no_solution = True

            elif block_type is BlockType.QUESTION:
                question_metadata = get_cell_config(cell)
                if not isinstance(question_metadata, dict):
                    raise AssignNotebookFormatException(
                        "Found a begin question cell with no config", question_metadata, i)
                question_metadata = create_question_config(question_metadata)
                if question_metadata["manual"] or question_metadata["export"]:
                    need_begin_export = True

            curr_block.append(block_type)
            continue

        # if in a block, process the current cell
        if len(curr_block) > 0:
            if curr_block[-1] == BlockType.TESTS:
                if not is_cell_type(cell, "code"):
                    raise AssignNotebookFormatException(
                        "Found a non-code cell in tests block", question_metadata, i)
                test_case = read_test(cell, question_metadata, assignment)
                test_cases.append(test_case)
                continue

            elif curr_block[-1] == BlockType.SOLUTION:
                cell = add_tag(cell, SOLUTION_CELL_TAG)

                if is_cell_type(cell, "markdown"):
                    solution_has_md_cells = True

            elif curr_block[-1] == BlockType.QUESTION and is_cell_type(cell, "markdown"):
                last_question_md_cell = len(transformed_cells)

        # add export tags if needed
        export_delim_cell = None
        if need_begin_export:
            if is_cell_type(cell, "markdown"):
                cell = add_export_tag_to_cell(cell, assignment)
            else:
                export_delim_cell = nbformat.v4.new_markdown_cell()
                export_delim_cell = add_export_tag_to_cell(export_delim_cell, assignment)
            need_begin_export = False
        if need_end_export:
            if is_cell_type(cell, "markdown"):
                cell = add_export_tag_to_cell(cell, assignment, end=True)
            else:
                if export_delim_cell is None:
                    export_delim_cell = nbformat.v4.new_markdown_cell()
                export_delim_cell = add_export_tag_to_cell(export_delim_cell, assignment, end=True)
            need_end_export = False

        if export_delim_cell is not None:
            transformed_cells.append(export_delim_cell)

        if has_seed(cell):
            assignment.seed_required = True

        # this is just a normal cell so add it to transformed_cells
        transformed_cells.append(cell)

    # if the last cell was the end of a manually-graded question, add a close export tag
    if need_end_export:
        transformed_cells.append(add_export_tag_to_cell(nbformat.v4.new_markdown_cell(), assignment, end=True))

    return transformed_cells, test_files
