"""
Assignment configurations for Otter Assign
"""

import yaml

from .constants import BLOCK_QUOTE
from .utils import get_source, get_spec

class Assignment:
    """
    A class that houses configurations for an assignment. Contains a dictionary of default arguments
    that can be updated in an instance using the ``update()`` method. Functions similarly to an 
    ``AttrDict`` in that keys of the configuration can be accessed as ``assignment.<key>``.

    To access a configuration value, use the dot syntax. For example, to access the ``generate`` key
    of an ``Assignment`` instance ``assignment``:
    
    .. code-block::python
        
        assignment.generate
    
    If ``generate`` is present in ``assignment.config``, then the value in that dictionary will be 
    returned. If it is not, the value in ``Assignment.defaults`` will be returned instead. Configurations
    can also be updated using dot syntax:
    
    .. code-block:: python
        
        assignment.generate = True

    If a key not present in ``Assignment.defaults`` is attempted to be accessed or set, an 
    ``AttributeError`` will be thrown.

    Attributes:
        config (``dict``): the configurations specific to this assignment; keys in this dictionary
            are used before the defaults if present.
    """
    defaults = {
        "master": None,
        "result": None,
        "generate": {},
        "solutions_pdf": False,
        "template_pdf": False,
        "seed_required": False,
        "save_environment": False,
        "requirements": None,
        "overwrite_requirements": False,
        "environment": None,
        "files": [],
        "autograder_files": [],
        "variables": {},
        "run_tests": True,
        "ignore_modules": [],
        "init_cell": True,
        "check_all_cell": True,
        "export_cell": True,
        "seed": None,
        "lang": None,
        "plugins": [],
        "plugin_config": {},
        "_otter_config": None,
        "test_files": True,
        "_temp_test_dir": None, # path to a temp dir for tests for otter generate
    }

    def __init__(self):
        self.config = type(self).defaults.copy()

    def __getattr__(self, attr):
        if attr in type(self).defaults:
            return self.config.get(attr, type(self).defaults[attr])
        raise AttributeError(f"Assignment has no attribute {attr}")

    def __setattr__(self, attr, value):
        if attr == "config":
            self.__dict__[attr] = value
        elif attr in type(self).defaults:
            self.config[attr] = value
        else:
            raise AttributeError(f"Assignment has no attribute {attr}")

    def update(self, config):
        """
        Updates the configuration stored in this assignment using keys and values in the dictionary
        ``config``

        Args:
            config (``dict``): new configurations
        """
        for k in config.keys():
            if k not in self.allowed_configs:
                raise ValueError(f"Unexpected assignment config: '{k}'")
        self.config.update(config)

    @property
    def is_r(self):
        """
        Whether the language of the assignment is R
        """
        return self.lang == "r"
    
    @property
    def is_python(self):
        """
        Whether the language of the assignment is Python
        """
        return self.lang == "python"

    @property
    def is_rmd(self):
        """
        Whether the input file is an RMarkdown document
        """
        return self.master.suffix.lower() == ".rmd"
    
    @property
    def allowed_configs(self):
        """
        The list of allowed configuration keys
        """
        return type(self).defaults.keys()

def read_assignment_metadata(cell):
    """
    Return assignment metadata from an assignment cell
    
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
    """
    Returns whether cell contains BEGIN ASSIGNMENT in a block quote
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is an assignment definition cell
    """
    if cell.cell_type != 'markdown':
        return False
    return get_spec(get_source(cell), "assignment") is not None
