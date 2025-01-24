"""Output directory creation for Otter Assign"""

import nbformat
import os
import pathlib
import shutil
import tempfile

from .assignment import Assignment
from .notebook_transformer import NotebookTransformer, TransformedNotebookContainer
from .r_adapter import rmarkdown_converter
from .r_adapter.tests_manager import RAssignmentTestsManager
from .tests_manager import AssignmentTestsManager
from .utils import get_notebook_language
from .. import logging
from ..utils import NBFORMAT_VERSION


LOGGER = logging.get_logger(__name__)


def write_output_dir(
    transformed_nb: TransformedNotebookContainer,
    output_dir: pathlib.Path,
    assignment: Assignment,
    sanitize: bool,
):
    """
    Write an output directory (either for the autograder or student, as indicated by ``sanitize``).

    Args:
        transformed_nb (``otter.assign.notebook_transformed.TransformedNotebookContainer``): the
            transformed notebook
        output_dir (``pathlib.Path``): the path to the output directory being written (assumed to
            already exist)
        assignment (``otter.assign.assignment.Assignment``): the assignment config
        sanitize (``bool``): whether to sanitize the output (by removing solutions and hidden tests)
    """
    output_path = output_dir / assignment.notebook_basename
    tests_dir = output_dir / "tests"
    if assignment.tests.files:
        os.makedirs(tests_dir, exist_ok=True)

    if not sanitize:
        if assignment.requirements:
            output_fn = ("requirements.txt", "requirements.R")[assignment.is_r]
            if isinstance(assignment.requirements, list):
                with open(str(output_dir / output_fn), "w+") as f:
                    f.write("\n".join(assignment.requirements))
                assignment.requirements = str(output_dir / output_fn)
            else:
                shutil.copy(assignment.requirements, str(output_dir / output_fn))

        if assignment.environment:
            output_fn = "environment.yml"
            shutil.copy(assignment.environment, str(output_dir / output_fn))

        if assignment.student_files:
            for file in assignment.student_files:
                # TODO: dedupe this logic with handling of autograder_files utils.py and logic below
                # for assignment.files
                if not os.path.isfile(file):
                    raise FileNotFoundError(f"{file} is not a file")
                if str(assignment.master.parent) not in os.path.abspath(file):
                    raise ValueError(
                        f"{file} is not in a subdirectory of the master notebook directory"
                    )
                file_path = pathlib.Path(file).resolve()
                rel_path = file_path.parent.relative_to(assignment.master.parent)
                os.makedirs(output_dir / rel_path, exist_ok=True)
                shutil.copy(file, str(output_dir / rel_path))

    # write tests
    transformed_nb.write_tests(str(tests_dir), not sanitize, assignment.tests.files)

    # write a temp dir for otter generate tests
    if not sanitize:
        assignment.generate_tests_dir = tempfile.mkdtemp()
        transformed_nb.write_tests(assignment.generate_tests_dir, True, True)

    transformed_nb.write_transformed_nb(output_path, sanitize)

    # copy files
    for file in assignment.files:

        # if a directory, copy the entire dir
        if os.path.isdir(file):
            shutil.copytree(file, str(output_dir / os.path.basename(file)))

        else:
            # check that file is in subdir
            if str(assignment.master.parent) not in os.path.abspath(file):
                raise ValueError(
                    f"{file} is not in a subdirectory of the master notebook directory"
                )
            file_path = pathlib.Path(file).resolve()
            rel_path = file_path.parent.relative_to(assignment.master.parent)
            os.makedirs(output_dir / rel_path, exist_ok=True)
            shutil.copy(file, str(output_dir / rel_path))


def write_output_directories(assignment: Assignment):
    """
    Process a master notebook and write the results to the output directories.

    Args:
        assignment (``otter.assign.assignment.Assignment``): the assignment config
    """
    if assignment.is_rmd:
        nb = rmarkdown_converter.read_as_notebook(assignment.master)
    else:
        nb = nbformat.read(assignment.master, as_version=NBFORMAT_VERSION)

    if assignment.lang is None:
        assignment.lang = get_notebook_language(nb)

    tests_mgr = (RAssignmentTestsManager if assignment.is_r else AssignmentTestsManager)(assignment)
    nb_transformer = NotebookTransformer(assignment, tests_mgr)
    transformed_nb = nb_transformer.transform_notebook(nb)

    # update assignment.tests.files for R notebooks
    assignment.tests.files |= assignment.is_r

    # force test files if a test URL prefix is provided
    if assignment.tests["url_prefix"]:
        assignment.tests.files = True

    # create directories
    autograder_dir = assignment.get_ag_path()
    student_dir = assignment.get_stu_path()
    shutil.rmtree(autograder_dir, ignore_errors=True)
    shutil.rmtree(student_dir, ignore_errors=True)
    os.makedirs(autograder_dir, exist_ok=True)
    os.makedirs(student_dir, exist_ok=True)

    # populate directories
    write_output_dir(transformed_nb, autograder_dir, assignment, False)
    write_output_dir(transformed_nb, student_dir, assignment, True)

    # print assignment summary
    LOGGER.info(nb_transformer.tests_mgr.generate_assignment_summary())
