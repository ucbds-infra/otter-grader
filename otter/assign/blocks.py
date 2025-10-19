"""Assignment block parsing for Otter Assign"""

import nbformat
import re
import yaml

from enum import Enum
from typing import Any, List

from .utils import AssignNotebookFormatException, is_cell_type
from ..utils import get_source


class BlockType(Enum):
    """
    An enum of allowed block types.
    """

    QUESTION = "question"
    PROMPT = "prompt"
    SOLUTION = "solution"
    TESTS = "tests"


def extract_fenced_otter_cell(cell: nbformat.NotebookNode) -> nbformat.NotebookNode:
    """
    Converts a Markdown config cell to a raw config cell.

    A Markdown cell with the contents

    .. code-block::

        ```otter
        <cell contents>
        ```

    would become a raw cell with the contents

    .. code-block::

        <cell contents>

    If the contents are not wrapped in a code block with the language set to ``otter``, the cell is
    returned unchanged.

    Args:
        cell (``nbformat.NotebookNode``): the cell to extract the config from

    Returns:
        ``nbformat.NotebookNode``: the unfenced cell contents
    """
    if not is_cell_type(cell, "markdown"):
        return cell

    source = get_source(cell)
    if (
        source[0].strip() == "```otter"
        and all(not l.strip() == "```" for l in source[1:-1])
        and source[-1].strip() == "```"
    ):
        return nbformat.v4.new_raw_cell("\n".join(source[1:-1]))

    return cell


def extract_all_fenced_otter_cells(cells: List[nbformat.NotebookNode]):
    """ """
    new_cells = []
    for cell_idx, cell in enumerate(cells):
        source = get_source(cell)
        starts = []
        for i, l in enumerate(source):
            if l.strip() == "```otter":
                starts.append(i)

        if not starts:
            new_cells.append(cell)
            continue

        ends = []
        for i in starts:
            for j, l in enumerate(source[i + 1 :]):
                if l.strip() == "```":
                    ends.append(i + 1 + j)
                    break

        # Check that every block is closed and that every block end occurs before the next block start.
        if len(starts) != len(ends) or not all(
            ends[i] < starts[i + 1] for i in range(len(starts) - 1)
        ):
            raise AssignNotebookFormatException('Unclosed "```otter" block', None, cell_idx)

        def add_cell(source, cell_type):
            # Ignore whitespace-only cells.
            if not any(l.strip() for l in source):
                return
            factory = getattr(nbformat.v4, f"new_{cell_type}_cell")
            new_cells.append(factory("\n".join(source)))

        for idx in range(len(starts)):
            i, j = starts[idx], ends[idx]

            begin, end = 0, len(source) + 1
            if idx > 0:
                begin = ends[idx - 1] + 1
            if idx < len(starts) - 1:
                end = starts[idx + 1]

            # If the line after the closing "```" is empty, skip it to prevent an extra newline
            # between paragraphs after the block is removed.
            after_start_offset = 1
            if j + 1 < len(source) and not source[j + 1].strip():
                after_start_offset = 2

            if idx == 0:
                # We only need to add the pre-block text if this is the first block, otherwise we will
                # end up duplicating the between-block cells.
                add_cell(source[begin:i], "markdown")
            add_cell(source[i + 1 : j], "raw")
            add_cell(source[j + after_start_offset : end], "markdown")

    return new_cells


def is_block_boundary_cell(
    cell: nbformat.NotebookNode,
    block_type: BlockType,
    end: bool = False,
) -> bool:
    """
    Determine whether ``cell`` is a boundary cell for a ``block_type`` block. If ``end`` is true,
    the block should be an end block; otherwise, it should be a begin block.

    Args:
        cell (``nbformat.NotebookNode``): the cell to check
        block_type (``BlockType``): the block type to check for
        end (``bool``): whether to check for an end boundary instead of a begin

    Returns:
        ``bool``: whether the cell is a boundary cell of type ``block_type``
    """
    cell = extract_fenced_otter_cell(cell)
    begin_or_end = "end" if end else "begin"
    regex = rf"#\s+{ begin_or_end }\s+{ block_type.value }\s*"
    source = get_source(cell)
    return is_cell_type(cell, "raw") and bool(re.match(regex, source[0], flags=re.IGNORECASE))


def is_assignment_config_cell(cell: nbformat.NotebookNode) -> bool:
    """
    Determine whether ``cell`` is an assignment configuration cell.

    An assignment configuration cell is a raw cell starting with the line ``# ASSIGNMENT CONFIG``,
    e.g.

    .. code-block:: yaml

        # ASSIGNMENT CONFIG
        requirements: requirements.txt
        files:
            - data.csv

    Args:
        cell (``nbformat.NotebookNode``): the cell to check

    Returns:
        ``bool``: whether the cell is an assignment config cell
    """
    cell = extract_fenced_otter_cell(cell)
    regex = r"#\s+assignment\s+config\s*"
    source = get_source(cell)
    return is_cell_type(cell, "raw") and bool(re.match(regex, source[0], flags=re.IGNORECASE))


def get_cell_config(cell: nbformat.NotebookNode) -> Any:
    """
    Parse a cell's contents as YAML and return the result.

    Does not check whether the result is a dictionary.

    Args:
        cell (``nbformat.NotebookNode``): the cell to check

    Returns:
        ``object``: the parsed configurations

    Raises:
        ``TypeError``: if parsing the YAML does not return a dictionary
    """
    source = get_source(extract_fenced_otter_cell(cell))
    config = yaml.full_load("\n".join(source))
    if config is None:
        config = {}
    return config
