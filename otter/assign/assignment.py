import yaml

from .defaults import BLOCK_QUOTE
from .utils import get_source, get_spec

class Assignment:
    """
    Kinda like an AttrDict but with defaults
    """
    defaults = {
        "generate": {},
        "solutions_pdf": False,
        "template_pdf": False,
        "seed_required": False,
        "service": {},
        "save_environment": False,
        "requirements": "requirements.txt",
        "overwrite_requirements": False,
        "files": [],
        "variables": {},
        "run_tests": True,
        "ignore_modules": [],
        "init_cell": True,
        "check_all_cell": True,
        "export_cell": True
    }

    def __init__(self, config):
        self.config = config

    def __getattr__(self, attr):
        if attr in type(self).defaults:
            return self.config.get(attr, defaults[attr])
        raise AttributeError(f"Assignment has no attribute {attr}")

    def __setattr__(self, attr, value):
        if attr in type(self).defaults:
            self.config[attr] = value
        else:
            raise AttributeError(f"Assignment has no attribute {attr}")

def read_assignment_metadata(cell):
    """Return assignment metadata from an assignment cell
    
    Args:
        cell (``nbformat.NotebookNode``): the assignment cell
    
    Returns:
        ``dict``: assignment metadata
    """
    source = get_source(cell)
    begin_assignment_line = get_spec(source, "assignment")
    i, lines = begin_assignment_line + 1, []
    while source[i].strip() != BLOCK_QUOTE:
        lines.append(source[i])
        i = i + 1
    metadata = yaml.full_load('\n'.join(lines))
    return metadata

def is_assignment_cell(cell):
    """Whether cell contains BEGIN ASSIGNMENT in a block quote
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is an assignment definition cell
    """
    if cell['cell_type'] != 'markdown':
        return False
    return get_spec(get_source(cell), "assignment") is not None
