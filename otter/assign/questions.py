"""
Question configurations for Otter Assign
"""

import copy
import yaml

from .constants import BLOCK_QUOTE, ALLOWED_NAME
from .utils import get_source, lock, get_spec, EmptyCellException
from ..utils import convert_config_description_dict


_DEFAULT_QUESTION_CONFIGURATIONS_WITH_DESCRIPTIONS = [
    {
        "key": "name",
        "description": "(required) the path to a requirements.txt file",
        "required": True,
    },
    {
        "key": "manual",
        "description": "whether this is a manually-graded question",
        "default": False,
    },
    {
        "key": "points",
        "description": "how many points this question is worth; defaults to 1 internally",
        "default": None,
    },
    {
        "key": "check_cell",
        "description": "whether to include a check cell after this question (for autograded questions only)",
        "default": True,
    },
    {
        "key": "export",
        "description": "whether to force-include this question in the exported PDF",
        "default": False,
    },
]

DEFAULT_QUESTION_CONFIGURATIONS = convert_config_description_dict(_DEFAULT_QUESTION_CONFIGURATIONS_WITH_DESCRIPTIONS)


def create_question_config(parsed_config):
    """
    """
    config = DEFAULT_QUESTION_CONFIGURATIONS.copy()
    config.update(parsed_config)
    if "name" not in config:
        raise ValueError(f"Question name not specified in config YAML: {parsed_config}")
    return config

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
