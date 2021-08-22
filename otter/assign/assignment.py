"""Assignment configurations for Otter Assign"""

import yaml

from .constants import BLOCK_QUOTE
from .utils import get_source, get_spec
from ..utils import convert_config_description_dict


_DEFAULT_ASSIGNMENT_CONFIGURATIONS_WITH_DESCRIPTIONS = [
    {
        "key": "requirements",
        "description": "the path to a requirements.txt file",
        "default": None,
    },
    {
        "key": "overwrite_requirements",
        "description": "whether to overwrite Otter's default requirement.txt in Otter Generate",
        "default": False,
    },
    {
        "key": "environment",
        "description": "the path to a conda environment.yml file",
        "default": None,
    },
    {
        "key": "run_tests",
        "description": "whether to run the assignment tests against the autograder notebook",
        "default": True,
    },
    {
        "key": "solutions_pdf",
        "description": "whether to generate a PDF of the solutions notebook",
        "default": False,
    },
    {
        "key": "template_pdf",
        "description": "whether to generate a filtered Gradescope assignment template PDF",
        "default": False,
    },
    {
        "key": "init_cell",
        "description": "whether to include an Otter initialization cell in the output notebooks",
        "default": True,
    },
    {
        "key": "check_all_cell",
        "description": "whether to include an Otter check-all cell in the output notebooks",
        "default": True,
    },
    {
        "key": "export_cell",
        "description": "whether to include an Otter export cell in the output notebooks",
        "default": [
            {
                "key": "instructions",
                "description": "additional submission instructions to include in the export cell",
                "default": "",
            },
            {
                "key": "pdf",
                "description": "whether to include a PDF of the notebook in the generated zip file",
                "default": True,
            },
            {
                "key": "filtering",
                "description": "whether the generated PDF should be filtered",
                "default": True,
            },
            {
                "key": "force_save",
                "description": "whether to force-save the notebook with JavaScript (only works in " \
                    "classic notebook)",
                "default": False,
            },
            {
                "key": "run_tests",
                "description": "whether to run student submissions against local tests during export",
                "default": False,
            },

        ],
    },
    {
        "key": "seed",
        "description": "a seed for intercell seeding",
        "default": None,
    },
    {
        "key": "generate",
        "description": "grading configurations to be passed to Otter Generate as an "\
            "otter_config.json; if false, Otter Generate is disabled",
        "default": False,
    },
    {
        "key": "save_environment",
        "description": "whether to save the student's environment in the log",
        "default": False,
    },
    {
        "key": "variables",
        "description": "a mapping of variable names to type strings for serlizing environments",
        "default": {},
    },
    {
        "key": "ignore_modules",
        "description": "a list of modules to ignore variables from during environment serialization",
        "default": [],
    },
    {
        "key": "files",
        "description": "a list of other files to include in the output directories and autograder",
        "default": [],
    },
    {
        "key": "autograder_files",
        "description": "a list of other files only to include in the autograder",
        "default": [],
    },
    {
        "key": "plugins",
        "description": "a list of plugin names and configurations",
        "default": [],
    },
    {
        "key": "test_files",
        "description": "whether to store tests in separate .py files rather than in the notebook " \
            "metadata",
        "default": False,
    },
    {
        "key": "colab",
        "description": "whether this assignment will be run on Google Colab",
        "default": False,
    },
]


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
        "seed_required": False,
        "_otter_config": None,
        "lang": None,
        "_temp_test_dir": None, # path to a temp dir for tests for otter generate
        **convert_config_description_dict(_DEFAULT_ASSIGNMENT_CONFIGURATIONS_WITH_DESCRIPTIONS),
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
