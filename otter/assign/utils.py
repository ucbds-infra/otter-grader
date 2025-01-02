"""Utilities for Otter Assign"""

import copy
import json
import nbformat as nbf
import os
import pathlib
import re
import shutil
import warnings

from textwrap import indent
from typing import Any, Optional, TYPE_CHECKING

from .. import logging
from ..api import grade_submission
from ..generate import main as generate_autograder
from ..plugins import PluginCollection
from ..run import capture_run_output
from ..utils import chdir, get_source, OTTER_CONFIG_FILENAME


LOGGER = logging.get_logger(__name__)


class EmptyCellException(Exception):
    """
    Exception for empty cells to indicate deletion
    """


class AssignNotebookFormatException(Exception):
    """
    An exception representing an error in the formatting of an Otter Assign master notebook.

    Wraps an error message with information about the question and cell to make the location of the
    error easy to find for users.

    Args:
        message (``str``): the error message
        question (``otter.assign.question_config.QuestionConfig | None``): the question config if
            the error occurred inside of a question block
        cell_index (``int``): the index of the cell
        *args: additional args passed to ``Exception`` constructor
        **kwargs: additional keyword args passed to ``Exception`` constructor
    """

    def __init__(
        self,
        message: str,
        question: Optional["QuestionConfig"],
        cell_index: int,
        *args: Any,
        **kwargs: Any,
    ):
        message += " ("
        if question is not None:
            message += f"question { question.name }, "
        message += f"cell number { cell_index + 1 })"
        super().__init__(message, *args, **kwargs)


def get_notebook_language(nb: nbf.NotebookNode) -> str:
    """
    Parse the notebook kernel language and return it as a string.

    Args:
        nb (``nbformat.NotebookNode``): the notebook

    Returns:
        ``str``: the name of the language as a lowercased string

    Warns:
        if there is no ``language`` key in the notebook's kernelspec
    """
    kernelspec = nb["metadata"]["kernelspec"]
    if "language" in kernelspec:
        return kernelspec["language"].lower()
    warnings.warn("Could not auto-parse kernelspec from notebook; assuming Python")
    return "python"


def is_ignore_cell(cell: nbf.NotebookNode) -> bool:
    """
    Returns whether the current cell should be ignored

    Args:
        cell (``nbformat.NotebookNode``): a notebook cell

    Returns:
        ``bool``: whether the cell is a ignored
    """
    source = get_source(cell)
    return bool(
        source and re.match(r"(##\s*ignore\s*##\s*|#\s*ignore\s*)", source[0], flags=re.IGNORECASE)
    )


def is_cell_type(cell: nbf.NotebookNode, cell_type: str) -> bool:
    """
    Determine whether a cell is of a specific type.

    Args:
        cell (``nbformat.NotebookNode``): the cell to check
        cell_type (``str``): the cell type to check for

    Returns:
        ``bool``: whether ``cell`` is of type ``cell_type``
    """
    return cell["cell_type"] == cell_type


def remove_output(nb: nbf.NotebookNode) -> None:
    """
    Remove all outputs from a notebook in-place.

    Args:
        nb (``nbformat.NotebookNode``): a notebook
    """
    for cell in nb["cells"]:
        if "outputs" in cell:
            cell["outputs"] = []
        if "execution_count" in cell:
            cell["execution_count"] = None


def lock(cell: nbf.NotebookNode) -> None:
    """
    Make a cell non-editable and non-deletable in-place.

    Args:
        cell (``nbformat.NotebookNode``): cell to be locked
    """
    m = cell["metadata"]
    m["editable"] = False
    m["deletable"] = False


def add_tag(cell: nbf.NotebookNode, tag: str) -> nbf.NotebookNode:
    """
    Add a tag to a cell, returning a copy.

    Args:
        cell (``nbformat.NotebookNode``): the cell to add a tag to
        tag (``str``): the tag to add

    Returns:
        ``nbformat.NotebookNode``: a copy of ``cell`` with the tag added
    """
    cell = copy.deepcopy(cell)
    if "tags" not in cell["metadata"]:
        cell["metadata"]["tags"] = []
    cell["metadata"]["tags"].append(tag)
    return cell


def has_tag(cell: nbf.NotebookNode, tag: str) -> bool:
    """
    Determine whether a cell has a tag.

    Args:
        cell (``nbformat.NotebookNode``): the cell to check
        tag (``str``): the tag to check for

    Returns:
        ``nbformat.NotebookNode``: whether ``cell`` is tagged with ``tag``
    """
    return tag in cell["metadata"].get("tags", [])


def remove_tag(cell: nbf.NotebookNode, tag: str) -> nbf.NotebookNode:
    """
    Remove a tag from a cell, returning a copy.

    Args:
        cell (``nbformat.NotebookNode``): the cell to remove a tag from
        tag (``str``): the tag to remove

    Returns:
        ``nbformat.NotebookNode``: a copy of ``cell`` with the tag removed
    """
    cell = copy.deepcopy(cell)
    if "tags" not in cell["metadata"] or tag not in cell["metadata"]["tags"]:
        return cell
    cell["metadata"]["tags"].remove(tag)
    return cell


def str_to_doctest(code_lines: list[str], lines: list[str]) -> list[str]:
    """
    Convert a list of lines of Python code ``code_lines`` to the doctest format and appending the
    results to ``lines``.

    Args:
        code_lines (``list[str]``): the code to convert
        lines (``list[str]``): the list to append the converted lines to

    Returns:
        ``list[str]``: a pointer to ``lines``
    """
    if len(code_lines) == 0:
        return lines
    line = code_lines.pop(0)
    # skip empty lines
    while not line:
        line = code_lines.pop(0)
    if line.startswith(" ") or line.startswith("\t"):
        return str_to_doctest(code_lines, lines + ["... " + line])
    elif (
        bool(re.match(r"^except[\s\w]*:", line))
        or line.startswith("elif ")
        or line.startswith("else:")
        or line.startswith("finally:")
    ):
        return str_to_doctest(code_lines, lines + ["... " + line])
    elif len(lines) > 0 and lines[-1].strip().endswith("\\"):
        return str_to_doctest(code_lines, lines + ["... " + line])
    else:
        return str_to_doctest(code_lines, lines + [">>> " + line])


def run_tests(assignment: "Assignment", debug: bool = False) -> None:
    """
    Grade a notebook and throw an error if it does not receive a perfect score.

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment config
        debug (``bool``): whether to throw errors instead of swallowing them during grading

    Raises:
        ``RuntimeError``: if the grade received by the notebook is not 100%
    """
    with capture_run_output() as run_output:
        results = grade_submission(
            str(assignment.ag_notebook_path),
            str(assignment.ag_zip_path),
            debug=debug,
            extra_submission_files=assignment.student_files,
        )

    LOGGER.debug(f"Otter Run output:\n{run_output.getvalue()}")

    if results.total != results.possible:
        raise RuntimeError(
            f"Some autograder tests failed in the autograder notebook:\n"
            + indent(results.summary(), "    ")
        )


def write_otter_config_file(assignment: "Assignment") -> None:
    """
    Create an Otter configuration file (a ``.otter`` file) for students to use Otter tools,
    including saving environments and submitting to an Otter Service deployment, using assignment
    configurations. Writes the resulting file to the ``autograder`` and ``student`` subdirectories
    of ``assignment.result``.

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment config
    """
    config = {}

    config["notebook"] = assignment.master.name
    config["save_environment"] = assignment.save_environment
    config["ignore_modules"] = assignment.ignore_modules

    if assignment.generate and assignment.generate.serialized_variables:
        config["variables"] = assignment.generate.serialized_variables

    config_name = assignment.master.stem + ".otter"
    with open(assignment.get_ag_path(config_name), "w+") as f:
        json.dump(config, f, indent=4)
    with open(assignment.get_stu_path(config_name), "w+") as f:
        json.dump(config, f, indent=4)


def run_generate_autograder(
    assignment: "Assignment",
    gs_username: Optional[str],
    gs_password: Optional[str],
    plugin_collection: Optional[PluginCollection] = None,
) -> None:
    """
    Run Otter Generate on the autograder directory to generate a Gradescope zip file. Relies on
    configurations in ``assignment.generate``.

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
        gs_username (``str | None``): Gradescope username for token generation
        gs_password (``str | None``): Gradescope password for token generation
        plugin_collection (``otter.plugins.PluginCollection``): a plugin collection to pass
            to Otter Generate
    """
    curr_dir = os.getcwd()
    with chdir(str(assignment.get_ag_path())):

        # use temp tests dir
        test_dir = "tests"
        if (
            assignment.is_python
            and not assignment.tests.files
            and assignment.generate_tests_dir is None
        ):
            raise RuntimeError("Failed to create temp tests directory for Otter Generate")

        elif assignment.is_python and not assignment.tests.files:
            test_dir = assignment.generate_tests_dir

        requirements = None
        if assignment.requirements:
            if assignment.is_r:
                requirements = "requirements.R"
            else:
                requirements = "requirements.txt"

        files = []
        if assignment.files:
            files += assignment.files

        if assignment.autograder_files:
            with chdir(curr_dir):
                output_dir = assignment.get_ag_path()

                # copy files
                for file in assignment.autograder_files:

                    # if a directory, copy the entire dir
                    if os.path.isdir(file):
                        shutil.copytree(file, str(output_dir / os.path.basename(file)))

                    else:
                        # check that file is in subdir
                        assert os.getcwd() in os.path.abspath(
                            file
                        ), f"{file} is not in a subdirectory of the master notebook directory"
                        file_path = pathlib.Path(file).resolve()
                        rel_path = file_path.parent.relative_to(pathlib.Path(os.getcwd()))
                        os.makedirs(output_dir / rel_path, exist_ok=True)
                        shutil.copy(file, str(output_dir / rel_path))

            files += assignment.autograder_files

        otter_config = assignment.get_otter_config()
        if otter_config:
            with open(OTTER_CONFIG_FILENAME, "w+") as f:
                json.dump(otter_config, f, indent=2)

        generate_autograder(
            tests_dir=test_dir,
            output_path=assignment.ag_zip_name,
            config=OTTER_CONFIG_FILENAME if otter_config else None,
            lang="python" if assignment.is_python else "r",
            requirements=requirements,
            overwrite_requirements=assignment.overwrite_requirements,
            environment="environment.yml" if assignment.environment else None,
            no_environment=False,
            username=gs_username,
            password=gs_password,
            files=files,
            plugin_collection=plugin_collection,
            assignment=assignment,
            python_version=assignment.get_python_version(),
            channel_priority_strict=assignment.channel_priority_strict,
            exclude_conda_defaults=assignment.exclude_conda_defaults,
        )

        # clean up temp tests dir
        if assignment.generate_tests_dir is not None:
            shutil.rmtree(assignment.generate_tests_dir)


def remove_cell_ids_if_applicable(nb: nbf.NotebookNode) -> None:
    """
    Remove all cell IDs from a notebook in-place iff the nbformat of the notebook is < 4.5.

    Args:
        nb (``nbformat.NotebookNode``): a notebook
    """
    if nb["nbformat"] < 4 or (nb["nbformat"] == 4 and nb["nbformat_minor"] < 5):
        for cell in nb.cells:
            if "id" in cell:
                cell.pop("id")


if TYPE_CHECKING:
    from .assignment import Assignment
    from .question_config import QuestionConfig
