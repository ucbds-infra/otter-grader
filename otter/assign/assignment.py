"""Assignment configurations for Otter Assign"""

import datetime as dt
import fica
import os
import pathlib
import yaml

from typing import Any, Literal, Optional, Union

from ..logging import Loggable
from ..run import AutograderConfig


class Assignment(fica.Config, Loggable):
    """
    Configurations for the assignment.
    """

    name: Optional[str] = fica.Key(
        description="a name for the assignment (to validate that students submit to the correct "
        "autograder)",
        default=None,
    )

    config_file: Optional[str] = fica.Key(
        description="path to a file containing assignment configurations; any configurations in "
        "this file are overridden by the in-notebook config",
        default=None,
    )

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

    solutions_pdf: Union[bool, Literal["filtered"]] = fica.Key(
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
            description="whether to force-save the notebook with JavaScript (only works in "
            "classic notebook)",
            default=False,
        )

        run_tests: bool = fica.Key(
            description="whether to run student submissions against local tests during export",
            default=True,
        )

        files: list[str] = fica.Key(
            description="a list of other files to include in the student submissions' zip file",
            factory=lambda: [],
        )

        class RequireNoPDFAckValue(fica.Config):

            message: str = fica.Key(
                description="a message to show to students if a PDF is meant to be included in "
                "the submission but cannot be generated",
            )

        require_no_pdf_ack: Union[bool, RequireNoPDFAckValue] = fica.Key(
            description="whether to require students to acknowledge that a PDF could not be "
            "created if one is meant to be included in the submission zip file",
            default=False,
            subkey_container=RequireNoPDFAckValue,
        )

        ignore_log: bool = fica.Key(
            description="whether to exclude the .OTTER_LOG file from the submission zip file",
            default=False,
            type_=bool,
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

    generate: AutograderConfig = fica.Key(
        description="grading configurations to be passed to Otter Generate as an "
        "otter_config.json",
        subkey_container=AutograderConfig,
    )

    save_environment: bool = fica.Key(
        description="whether to save the student's environment in the log",
        default=False,
    )

    ignore_modules: list[str] = fica.Key(
        description="a list of modules to ignore variables from during environment serialization",
        factory=lambda: [],
    )

    files: list[str] = fica.Key(
        description="a list of other files to include in the output directories and autograder",
        factory=lambda: [],
    )

    autograder_files: list[str] = fica.Key(
        description="a list of other files only to include in the autograder",
        factory=lambda: [],
    )

    student_files: list[str] = fica.Key(
        description="a list of files that will be generated by students and thus should not be included in the autograder configuration zip file",
        factory=lambda: [],
        type_=list,
    )

    plugins: list[str] = fica.Key(
        description="a list of plugin names and configurations",
        factory=lambda: [],
    )

    class TestsValue(fica.Config):

        files: bool = fica.Key(
            description="whether to store tests in separate files, instead of the notebook "
            "metadata",
            default=False,
        )

        ok_format: bool = fica.Key(
            description="whether the test cases are in OK-format (instead of the exception-based "
            "format)",
            default=True,
        )

        url_prefix: Optional[str] = fica.Key(
            description="a URL prefix for where test files can be found for student use",
            default=None,
        )

    tests: TestsValue = fica.Key(
        description="information about the structure and storage of tests",
        subkey_container=TestsValue,
        enforce_subkeys=True,
    )

    show_question_points: bool = fica.Key(
        description="whether to add the question point values to the last cell of each question",
        default=False,
    )

    runs_on: str = fica.Key(
        description="the interpreter this notebook will be run on if different from the "
        "default interpreter (one of {'default', 'colab', 'jupyterlite'})",
        default="default",
        validator=fica.validators.choice(["default", "colab", "jupyterlite"]),
    )

    python_version: Optional[Union[str, int, float]] = fica.Key(
        description="the version of Python to use in the grading image (must be 3.9+)",
        default=None,
    )

    channel_priority_strict: bool = fica.Key(
        description="whether to set conda's channel_priority config to strict in the setup.sh file",
        default=True,
    )

    exclude_conda_defaults: bool = fica.Key(
        description="whether to exclude conda's defaults channel in the generated environment.yml file",
        default=False,
    )

    lang: Optional[str] = None
    """the language of the assignment"""

    master: pathlib.Path = None
    """the path to the master notebook"""

    result: pathlib.Path = None
    """the path to the output directory"""

    seed_required: bool = False
    """whether a seeding configuration is required for Otter Generate"""

    generate_tests_dir: Optional[str] = None
    """the path to a directory of test files for Otter Generate"""

    _ag_zip_name: Optional[str] = None
    """
    the file name for the autograder zip file; this value is generated the first time it is accessed
    since it contians a timestamp
    """

    def __init__(self, user_config: Optional[dict[str, Any]] = None, **kwargs: Any) -> None:
        if user_config is None:
            user_config = {}
        self._logger.debug(f"Initializing with config: {user_config}")
        super().__init__(user_config, **kwargs)

        # convert true values masking subkey contains to those containers
        if self.generate is True:
            self.generate = AutograderConfig()
        if self.export_cell is True:
            self.export_cell = type(self).ExportCellValue()

    def update(self, user_config: dict[str, Any]):
        self._logger.debug(f"Updating config: {user_config}")
        ret = super().update(user_config)
        if self.generate is True:
            self.generate = AutograderConfig()
        if self.export_cell is True:
            self.export_cell = type(self).ExportCellValue()
        return ret

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

    def get_otter_config(self):
        """
        Get the contents of ``otter_config.json`` for this assignment.

        Returns:
            ``dict[str, object]``: the ``otter_config.json`` file as a ``dict``
        """
        if self.is_r:
            self.generate.lang = "r"

        if self.name:
            self.generate.assignment_name = self.name

        return self.generate.get_user_config()

    @property
    def notebook_basename(self):
        """the basename of the notebook"""
        return os.path.basename(str(self.master))

    @property
    def ag_notebook_path(self):
        """the path to the autograder notebook"""
        return self.get_ag_path(self.notebook_basename)

    @property
    def ag_zip_name(self):
        """the file name of the autograder zip file"""
        if self._ag_zip_name is None:
            timestamp = dt.datetime.now().strftime("%Y_%m_%dT%H_%M_%S_%f")
            self._ag_zip_name = f"{self.master.stem}-autograder_{timestamp}.zip"
        return self._ag_zip_name

    @property
    def ag_zip_path(self):
        """the path to the autograder zip file"""
        return self.get_ag_path(self.ag_zip_name)

    def get_ag_path(self, path: Union[str, pathlib.Path] = "") -> pathlib.Path:
        """
        Get the path to the autograder output directory or a file in that directory.

        Args:
            path (``str | pathlib.Path``): a path to append to the autograder output directory path

        Returns:
            ``pathlib.Path``: the path to the autograder directory or the specified file within it
        """
        return self.result / "autograder" / path

    def get_stu_path(self, path: Union[str, pathlib.Path] = "") -> pathlib.Path:
        """
        Get the path to the student output directory or a file in that directory.

        Args:
            path (``str | pathlib.Path``): a path to append to the student output directory path

        Returns:
            ``pathlib.Path``: the path to the student directory or the specified file within it
        """
        return self.result / "student" / path

    def get_python_version(self) -> Optional[str]:
        """
        Returns the Python version indicated as a string (to avoid issues with YAML interpreting it
        as a number) if one is present.

        Returns:
            ``str | None``: the version string or ``None`` if none is present
        """
        return str(self.python_version) if self.python_version is not None else None

    def load_config_file(self, config_file: str):
        """
        Update the values in this config using the values in the specified file.

        Args:
            config_file (``str``): the configuration file to read
        """
        self._logger.info(f"Reading assignment config file {config_file}")

        with open(config_file) as f:
            config = yaml.full_load(f.read())

        if not isinstance(config, dict):
            raise TypeError("Configuration files did not produce a dictionary")

        self.update({**config, "config_file": config_file})
