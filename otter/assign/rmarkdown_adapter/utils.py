import nbformat
import re

from collections import namedtuple

from .constants import BEGIN_REGEX, END_REGEX

from ..constants import BLOCK_QUOTE
from ..utils import get_source, get_spec


CELL_CREATORS = {
    "markdown": nbformat.v4.new_markdown_cell,
    "code": nbformat.v4.new_code_cell,
}


def create_cell(cell_type, source):
    """
    """
    return CELL_CREATORS[cell_type](source)


def rmd_to_cells(rmd_string):
    """
    Converts an Rmd document as a string into a list of ``Cell`` objects for easier handling with
    code designed originally for Jupyter notebooks.

    Args:
        rmd_string (``str``): the Rmd document as a string

    Returns:
        ``list`` of ``Cell``: the "cells" represented named tuples
    """
    cells, cell_lines, cell_type, in_block, in_begin = [], [], "markdown", False, False
    for line in rmd_string.split("\n"):
        if in_block and (line.strip() == "```" or re.match(END_REGEX, line)):
            in_block = False

            # collect cell_lines into a new cell
            cell = create_cell(cell_type, "\n".join(cell_lines + [line]))
            cells.append(cell)
            cell_type, cell_lines = "markdown", []

        elif line.startswith("```") or re.match(BEGIN_REGEX, line):
            in_block = True

            # collect cell_lines into a new cell
            if cell_lines:
                cell = create_cell(cell_type, "\n".join(cell_lines))
                cells.append(cell)
            cell_type = "code" if line.startswith("```{r") and "}" in line else "markdown"
            cell_lines = [line]

        else:
            cell_lines.append(line)

    # collect remaining cell lines into a new cell
    if cell_lines:
        cell = create_cell(cell_type, "\n".join(cell_lines))
        cells.append(cell)

    return cells


def collapse_empty_cells(cells):
    """
    Collapses all runs of cells with empty sources into a single cell with an empty source

    Args:
        cells (``list`` of ``Cell``): the cells

    Returns:
        ``list`` of ``Cell``: cells with runs collapsed
    """
    in_run, run_start = False, 0
    replacements = []
    for i, cell in enumerate(cells):
        if in_run and cell["source"].strip():
            if (run_start > 0 and cells[run_start-1]["source"].endswith("\n")) or cell["source"].startswith("\n"):
                replacement = []
            else:
                replacement = [create_cell("markdown", "")]
            replacements.append((run_start, i, replacement))
            in_run = False
        elif not in_run and not cell["source"].strip():
            in_run = True
            run_start = i
    
    replacements.reverse()
    for rs, re, rep in replacements:
        cells[rs:re] = rep
