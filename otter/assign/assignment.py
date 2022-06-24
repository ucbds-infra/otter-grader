"""Assignment configurations for Otter Assign"""

import fica
import yaml

from typing import Dict, List, Optional

from .constants import BLOCK_QUOTE
from .utils import get_source, get_spec
from ..utils import convert_config_description_dict, Loggable, loggers, recursive_dict_update


LOGGER = loggers.get_logger(__name__)


class Assignment(fica.Config):
    """
    Configurations for the assignment.
    """

    requirements: Optional[str] = fica.Key(
        description="the path to a requirements.txt file or a list of packages",
        default=None,
    )

    overwrite_requirements: bool = fica.Key(
        description="whether to overwrite Otter's default requirement.txt in Otter Generate",
        default=False,
    )

    environment: Optional[str] = fica.Key(
        description="the path to a conda environment.yml file",
        default=None,
    )

    run_tests: bool = fica.Key(
        description="whether to run the assignment tests against the autograder notebook",
        default=True,
    )

    solutions_pdf: bool = fica.Key(
        description="whether to generate a PDF of the solutions notebook",
        default=False,
    )

    template_pdf: bool = fica.Key(
        description="whether to generate a filtered Gradescope assignment template PDF",
        default=False,
    )

    init_cell: bool = fica.Key(
        description="whether to include an Otter initialization cell in the output notebooks",
        default=True,
    )

    check_all_cell: bool = fica.Key(
        description="whether to include an Otter check-all cell in the output notebooks",
        default=False,
    )

    class ExportCellValue(fica.Config):

        instructions: str = fica.Key(
            description="additional submission instructions to include in the export cell",
            default="",
        )

        pdf: bool = fica.Key(
            description="whether to include a PDF of the notebook in the generated zip file",
            default=True,
        )

        filtering: bool = fica.Key(
            description="whether the generated PDF should be filtered",
            default=True,
        )

        force_save: bool = fica.Key(
            description="whether to force-save the notebook with JavaScript (only works in " \
                "classic notebook)",
            default=False,
        )

        run_tests: bool = fica.Key(
            description="whether to run student submissions against local tests during export",
            default=True,
        )

    export_cell: ExportCellValue = fica.Key(
        description="whether to include an Otter export cell in the output notebooks",
        subkey_container=ExportCellValue,
    )

    class SeedValue(fica.Config):

        variable: Optional[str] = fica.Key(
            description="a variable name to override with the autograder seed during grading",
            default=None,
        )

        autograder_value: Optional[int] = fica.Key(
            description="the value of the autograder seed",
            default=None,
        )

        student_value: Optional[int] = fica.Key(
            description="the value of the student seed",
            default=None,
        )

    seed: SeedValue = fica.Key(
        description="intercell seeding configurations",
        default=None,
        subkey_container=SeedValue,
    )

    generate: bool = fica.Key(
        description="grading configurations to be passed to Otter Generate as an " \
            "otter_config.json; if false, Otter Generate is disabled",
        default=False,
    )

    save_environment: bool = fica.Key(
        description="whether to save the student's environment in the log",
        default=False,
    )

    variables: Optional[Dict[str, str]] = fica.Key(
        description="a mapping of variable names to type strings for serializing environments",
        default=None, # TODO: this was {}, is this an issue?
    )

    ignore_modules: List[str] = fica.Key(
        description="a list of modules to ignore variables from during environment serialization",
        default=[],
    )

    files: List[str] = fica.Key(
        description="a list of other files to include in the output directories and autograder",
        default=[],
    )

    autograder_files: List[str] = fica.Key(
        description="a list of other files only to include in the autograder",
        default=[],
    )

    plugins: List[str] = fica.Key(
        description="a list of plugin names and configurations",
        default=[],
    )

    class TestsValue(fica.Config):

        files: bool = fica.Key(
            description="whether to store tests in separate files, instead of the notebook " \
                "metadata",
            default=False,
        )

        ok_format: bool = fica.Key(
            description="whether the test cases are in OK-format (instead of the exception-based " \
                "format)",
            default=True,
        )

    tests: TestsValue = fica.Key(
        description="information about the structure and storage of tests",
        subkey_container=TestsValue,
        enforce_subkeys=True,
    )

    colab: bool = fica.Key(
        description="whether this assignment will be run on Google Colab",
        default=False,
    )

    show_question_points: bool = fica.Key(
        description="whether to add the question point values to the last cell of each question",
        default=False,
    )

    lang = None


    # TODO: add in other defaults
    defaults = {
        "master": None,
        "result": None,
        "seed_required": False,
        "_otter_config": None,
        "lang": None,
        "_temp_test_dir": None, # path to a temp dir for tests for otter generate
        "notebook_basename": None,
        "test_files": {},  # test file name -> test file info
        # **convert_config_description_dict(_DEFAULT_ASSIGNMENT_CONFIGURATIONS_WITH_DESCRIPTIONS),
    }


    # TODO: how to recursively update values? is this necessary?
    # def update(self, config):
    #     """
    #     Updates the configuration stored in this assignment using keys and values in the dictionary
    #     ``config``

    #     Args:
    #         config (``dict``): new configurations
    #     """
    #     self._logger.debug(f"Updating configurations: {config}")
    #     for k in config.keys():
    #         if k not in self.allowed_configs:
    #             raise ValueError(f"Unexpected assignment config: '{k}'")
    #     recursive_dict_update(self.config, config)

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
    
    # @property
    # def allowed_configs(self):
    #     """
    #     The list of allowed configuration keys
    #     """
    #     return type(self).defaults.keys()


# TODO: remove after finishing Rmd v1 format
def read_assignment_metadata(cell):
    """
    Return assignment metadata from an assignment cell
    
    Args:
        cell (``nbformat.NotebookNode``): the assignment cell
    
    Returns:
        ``dict``: assignment metadata
    """
    LOGGER.debug(f"Parsing assignment metadata from cell: {cell}")
    source = get_source(cell)
    begin_assignment_line = get_spec(source, "assignment")
    i, lines = begin_assignment_line + 1, []
    while source[i].strip() != BLOCK_QUOTE:
        lines.append(source[i])
        i = i + 1
    metadata = yaml.full_load('\n'.join(lines))
    LOGGER.debug(f"Parsed assignment metadata: {metadata}")
    return metadata


# TODO: remove after finishing Rmd v1 format
# TODO: also remove get_spec
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
