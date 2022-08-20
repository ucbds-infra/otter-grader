"""Convert a v0 formatted notebook to a v1 formatted notebook"""

import copy
import nbformat
import re

from ..assignment import is_assignment_cell
from ..constants import BEGIN_TEST_CONFIG_REGEX, BLOCK_QUOTE
from ..questions import is_question_cell, read_question_metadata
from ..solutions import is_markdown_solution_cell
from ..tests import is_test_cell
from ..utils import get_source, get_spec, is_markdown_cell

from ...blocks import BlockType


def generate_delim_cell(block_type, end=False):
    """
    Generates a block boundary cell for the specified block type.

    Args:
        block_type (``BlockType``): the block type to deliminate
        end (``bool``): wheter this is an end block cell

    Returns:
        ``nbformat.NotebookNode``: the generated boundary cell
    """
    source = f"# {'END' if end else 'BEGIN'} { block_type.value.upper() }"
    return nbformat.v4.new_raw_cell(source)


def transform_test_cell(cell):
    """
    Transform a test cell from v0 to v1 format.

    Args:
        cell (``nbformat.NotebookNode``): the cell to transform

    Returns:
        ``nbformat.NotebookNode``: the transformed cell
    """
    cell = copy.deepcopy(cell)
    source = get_source(cell)
    if re.match(BEGIN_TEST_CONFIG_REGEX, source[0]):
        return cell
    else:
        if "hidden" in source[0].lower():
            source = ["# HIDDEN"] + source[1:]
        else:
            source = source[1:]
    cell["source"] = "\n".join(source)
    return cell


def transform_assignment_cell(cell):
    """
    Transform an assignment config cell from v0 to v1 format.

    Args:
        cell (``nbformat.NotebookNode``): the cell to transform

    Returns:
        ``nbformat.NotebookNode``: the transformed cell
    """
    source = get_source(cell)
    begin_assignment_line = get_spec(source, "assignment")
    i, lines = begin_assignment_line + 1, []
    while source[i].strip() != BLOCK_QUOTE:
        lines.append(source[i])
        i = i + 1
    return nbformat.v4.new_raw_cell("\n".join(["# ASSIGNMENT CONFIG"] + lines))


def extract_question_metadata(cell):
    """
    Extract the question metadata lines from a question cell and return the original source lines
    stripped of the metadata block as well as the lines of YAML metadata.

    Args:
        cell (``nbformat.NotebookNode``): the cell to transform

    Returns:
        ``tuple[list[str], list[str]]``: the stripped question and the YAML lines
    """
    source = get_source(cell)
    begin_question_line = get_spec(source, "question")
    i, lines = begin_question_line + 1, []
    while source[i].strip() != BLOCK_QUOTE:
        lines.append(source[i])
        i = i + 1
    source = source[:begin_question_line-1] + source[i+1:]
    return source, lines


def get_transformed_cells(cells):
    """
    Transform a list of cells defining a v0-formatted notebook into a v1-formatted notebook.

    Args:
        cells (``list[nbformat.NotebookNode]``): the original notebook cells

    Returns:
        ``list[nbformat.NotebookNode]``: the transformed notebook cells
    """
    transformed_cells = []
    question_metadata, processed_solution, tests_started = False, False, False

    for cell in cells:

        # this is the prompt cell or if a manual question then the solution cell
        if question_metadata and not processed_solution:
            assert not is_question_cell(cell), f"Found question cell before end of previous question cell: {cell}"

            # if this isn't a MD solution cell but in a manual question, it has a Markdown prompt
            if question_metadata.get('manual', False) and is_markdown_cell(cell) and not is_markdown_solution_cell(cell):
                md_has_prompt = True
                transformed_cells.append(generate_delim_cell(BlockType.PROMPT))
                transformed_cells.append(cell)
                transformed_cells.append(generate_delim_cell(BlockType.PROMPT, end=True))
                continue

            # if this is a test cell, this question has no response cell for the students, so we don't
            # include it in the output notebook but we need a test file
            elif is_test_cell(cell):
                transformed_cells.append(generate_delim_cell(BlockType.TESTS))
                transformed_cells.append(transform_test_cell(cell))
                no_solution = True
                tests_started = True

            else:
                transformed_cells.append(generate_delim_cell(BlockType.SOLUTION))
                transformed_cells.append(cell)
                transformed_cells.append(generate_delim_cell(BlockType.SOLUTION, end=True))

            processed_solution = True

        # if this is a test cell, parse and add to test_cases
        elif question_metadata and processed_solution and is_test_cell(cell):
            if not tests_started:
                transformed_cells.append(generate_delim_cell(BlockType.TESTS))
                tests_started = True
            transformed_cells.append(transform_test_cell(cell))

        else:
            # the question is over -- we've seen the question and solution and any tests and now we 
            # need to get ready to process the next question which *could be this cell*
            if question_metadata and processed_solution:

                if tests_started:
                    transformed_cells.append(generate_delim_cell(BlockType.TESTS, end=True))
                transformed_cells.append(generate_delim_cell(BlockType.QUESTION, end=True))

                # reset vars
                question_metadata, processed_solution, tests_started = False, False, False

            if is_assignment_cell(cell):
                transformed_cells.append(transform_assignment_cell(cell))

            # if a question cell, parse metadata, comment out question metadata, and append to nb
            elif is_question_cell(cell):
                new_source, meta_lines = extract_question_metadata(cell)
                new_cell = generate_delim_cell(BlockType.QUESTION)
                source = get_source(new_cell)
                source.extend(meta_lines)
                new_cell["source"] =  "\n".join(source)

                transformed_cells.append(new_cell)
                transformed_cells.append(nbformat.v4.new_markdown_cell("\n".join(new_source)))

                question_metadata = read_question_metadata(cell)

            else:
                assert not is_test_cell(cell), f"Test outside of a question: {cell}"
                transformed_cells.append(cell)

    if tests_started:
        transformed_cells.append(generate_delim_cell(BlockType.TESTS, end=True))

    if question_metadata is not False:
        transformed_cells.append(generate_delim_cell(BlockType.QUESTION, end=True))

    return transformed_cells
