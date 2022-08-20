"""
Question configurations for Otter Assign
"""

import copy
import yaml

from .constants import BLOCK_QUOTE, ALLOWED_NAME
from .utils import get_source, lock, get_spec, EmptyCellException

def is_question_cell(cell):
    """
    Returns whether cell contains BEGIN QUESTION in a block quote

    Args:
        cell (``nbformat.NotebookNode``): a notebook cell

    Returns:
        ``bool``: whether the current cell is a question definition cell
    """
    if cell.cell_type != 'markdown':
        return False
    return get_spec(get_source(cell), "question") is not None

def gen_question_cell(cell, manual, need_close_export):
    """
    Returns a locked question cell with metadata hidden in an HTML comment

    Args:
        cell (``nbformat.NotebookNode``): the original question cell

    Returns:
        ``nbformat.NotebookNode``: the updated question cell
    """
    cell = copy.deepcopy(cell)
    source = get_source(cell)
    if manual:
        source = ["<!-- BEGIN QUESTION -->", ""] + source
    if need_close_export:
        source = ["<!-- END QUESTION -->", ""] + source
    begin_question_line = get_spec(source, "question")
    start = begin_question_line - 1
    assert source[start].strip() == BLOCK_QUOTE
    end = begin_question_line
    while source[end].strip() != BLOCK_QUOTE:
        end += 1
    source[start] = "<!--"
    source[end] = "-->"
    cell['source'] = '\n'.join(source)

    # check if cell is empty, and if so, throw error
    cell_text = source[:start]
    try:
        cell_text += source[end+1:]
    except IndexError:
        pass
    if not "".join(cell_text).strip():
        raise EmptyCellException()

    lock(cell)
    return cell

def read_question_metadata(cell):
    """
    Returns parsed question metadata from a question cell

    Args:
        cell (``nbformat.NotebookNode``): the question cell

    Returns:
        ``dict``: question metadata
    """
    source = get_source(cell)
    begin_question_line = get_spec(source, "question")
    i, lines = begin_question_line + 1, []
    while source[i].strip() != BLOCK_QUOTE:
        lines.append(source[i])
        i = i + 1
    metadata = yaml.full_load('\n'.join(lines))
    assert ALLOWED_NAME.match(metadata.get('name', '')), metadata
    return metadata
