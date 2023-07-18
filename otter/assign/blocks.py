"""Assignment block parsing for Otter Assign"""

import nbformat
import re
import yaml

from enum import Enum

from .utils import get_source, is_cell_type


class BlockType(Enum):
    """
    An enum of allowed block types.
    """

    QUESTION = "question"
    PROMPT = "prompt"
    SOLUTION = "solution"
    TESTS = "tests"


def extract_fenced_otter_cell(cell):
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
    if source[0].strip() == "```otter" and \
            all(not l.strip() == "```" for l in source[1:-1]) and source[-1].strip() == "```":
        return nbformat.v4.new_raw_cell("\n".join(source[1:-1]))

    return cell


def is_block_boundary_cell(cell, block_type, end=False):
    """
    Determine whether ``cell`` is a boundary cell for a ``block_type`` block. If ``end`` is true,
    the block should be an end block; otherwise, it should be a begin block.

    Args:
        cell (``nbformat.NotebookNode``): the cell to check
        block_type (``BlockType``): the block type to check for
        end (``bool``, optional): whether to check for an end boundary instead of a begin

    Returns:
        ``bool``: whether the cell is a boundary cell of type ``block_type``
    """
    cell = extract_fenced_otter_cell(cell)
    begin_or_end = 'end' if end else 'begin'
    regex = fr"#\s+{ begin_or_end }\s+{ block_type.value }\s*"
    source = get_source(cell)
    return is_cell_type(cell, "raw") and bool(re.match(regex, source[0], flags=re.IGNORECASE))


def is_assignment_config_cell(cell):
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


def get_cell_config(cell):
    """
    Parse a cell's contents as YAML and return the resulting dictionary.

    Args:
        cell (``nbformat.NotebookNode``): the cell to check

    Returns:
        ``dict[str, object]``: the parsed configurations

    Raises:
        ``TypeError``: if parsing the YAML does not return a dictionary
    """
    source = get_source(extract_fenced_otter_cell(cell))
    config = yaml.full_load("\n".join(source))
    if not isinstance(config, dict) and config is not None:
        raise TypeError(f"Found a begin cell configuration that is not a dictionary: {cell}")
    return config
