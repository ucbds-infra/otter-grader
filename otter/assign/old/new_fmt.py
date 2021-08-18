import nbformat
import re
import yaml

from enum import Enum

from otter.assign.cell_generators import add_close_export_to_cell, gen_markdown_response_cell
from otter.assign.tests import any_public_tests, read_test
from otter.utils import get_source

ALLOWED_BLOCKS = {'question', 'prompt', 'solution', 'tests'}

class BlockType(Enum):

    QUESTION = "question"
    PROMPT = "prompt"
    SOLUTION = "solution"
    TESTS = "tests"

class AssignNotebookFormatException(Exception):
    """
    """
    def __init__(self, message, cell_index, *args, **kwargs):
        message = message + f" (cell number { cell_index + 1 }"
        super().__init__(message, *args, **kwargs)

def is_block_boundary_cell(cell, block_type, end=False):
    """
    """
    begin_or_end = 'end' if end else 'begin'
    regex = fr"#\s+{ begin_or_end }\s+{ block_type.value }\s*"
    source = get_source(cell)
    return cell["cell_type"] == "raw" and bool(re.match(regex, source[0], flags=re.IGNORECASE))

def is_assignment_config_cell(cell):
    """
    """
    regex = r"#\s+assignment\s+config\s*"
    source = get_source(cell)
    return cell["cell_type"] == "raw" and bool(re.match(regex, source[0], flags=re.IGNORECASE))

def get_boundary_cell_config(cell):
    """
    """
    source = get_source(cell)
    config = yaml.full_load("\n".join(source))
    if not isinstance(config, dict):
        # TODO: make this error nicer?
        raise TypeError(f"Found a begin cell configuration that is not a dictionary: {cell}")
    return config

def transform_cells(cells, assignment):
    """
    """
    if assignment.is_r:
        from otter.assign.r_adapter.tests import read_test, gen_test_cell
    else:
        from otter.assign.tests import read_test, gen_test_cell

    curr_block = []  # allow nested blocks
    new_cells = []
    test_files = {}

    question_metadata, test_cases, has_prompt, no_solution = \
        {}, [], False, False

    need_begin_export, need_close_export = False, False

    for i, cell in enumerate(cells):            

        # check for an end to the current block
        if len(curr_block) > 0 and is_block_boundary_cell(cell, curr_block[-1], end=True):
            block_type = curr_block.pop()  # remove the block

            if block_type is BlockType.QUESTION:

                if question_metadata.get("manual", False):  # TODO: convert question_metadata to defaultdict
                    need_close_export = True

                # generate a check cell
                if test_cases:
                    check_cell = gen_test_cell(question_metadata, test_cases, test_files, assignment)

                    # only add to notebook if there's a response cell or if there are public tests
                    # don't add cell if the 'check_cell' key of quetion_metadata is false
                    if (not no_solution or any_public_tests(test_cases)) and \
                            question_metadata.get('check_cell', True):
                        new_cells.append(check_cell)

                    question_metadata, test_cases, has_prompt, no_solution = \
                        {}, [], False, False

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
                new_cells.append(gen_markdown_response_cell())
                has_prompt = True

            elif block_type is BlockType.TESTS and not has_prompt:
                no_solution = True  # TODO: what is this for?

            elif block_type is BlockType.QUESTION:
                question_metadata = get_boundary_cell_config(cell)
                if question_metadata.get("manual", False):
                    need_begin_export = True

            curr_block.append(block_type)
            continue

        # if in a block, process the current cell
        if len(curr_block) > 0 and curr_block[-1] == BlockType.TESTS:
            test_case = read_test(cell, question_metadata, assignment)
            test_cases.append(test_case)
            continue

        # this is just a normal cell so add it to new_cells
        new_cells.append(cell)



# TODO: need_close_export

nb = nbformat.read("~/Desktop/proj03-game-theory/proj03.ipynb", as_version=4)
