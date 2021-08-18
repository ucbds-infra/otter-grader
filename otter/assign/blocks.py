""""""

import re
import yaml

from enum import Enum

from .utils import get_source, is_cell_type


class BlockType(Enum):

    QUESTION = "question"
    PROMPT = "prompt"
    SOLUTION = "solution"
    TESTS = "tests"


def is_block_boundary_cell(cell, block_type, end=False):
    """
    """
    begin_or_end = 'end' if end else 'begin'
    regex = fr"#\s+{ begin_or_end }\s+{ block_type.value }\s*"
    source = get_source(cell)
    return is_cell_type(cell, "raw") and bool(re.match(regex, source[0], flags=re.IGNORECASE))


def is_assignment_config_cell(cell):
    """
    """
    regex = r"#\s+assignment\s+config\s*"
    source = get_source(cell)
    return is_cell_type(cell, "raw") and bool(re.match(regex, source[0], flags=re.IGNORECASE))


def get_cell_config(cell):
    """
    """
    source = get_source(cell)
    config = yaml.full_load("\n".join(source))
    if not isinstance(config, dict):
        # TODO: make this error nicer?
        raise TypeError(f"Found a begin cell configuration that is not a dictionary: {cell}")
    return config
