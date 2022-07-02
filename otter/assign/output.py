"""Output directory creation for Otter Assign"""

import nbformat
import os
import pathlib
import shutil
import tempfile
import warnings

from .assignment import Assignment
from .constants import NB_VERSION
from .notebook_transformer import NotebookTransformer
from .r_adapter import rmarkdown_converter
from .r_adapter.tests_manager import RAssignmentTestsManager
from .tests_manager import AssignmentTestsManager
from .utils import get_notebook_language


def write_output_dir(
    nb_transformer: NotebookTransformer,
    output_dir: pathlib.Path,
    assignment: Assignment,
    sanitize: bool,
):
    """
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

    # write tests
    nb_transformer.write_tests(str(tests_dir), not sanitize, assignment.tests.files)

    # write a temp dir for otter generate tests
    if not sanitize and assignment.generate:
        assignment._temp_test_dir = pathlib.Path(tempfile.mkdtemp())
        nb_transformer.write_tests(str(assignment._temp_test_dir), True, True)

    nb_transformer.write_transformed_nb(output_path, sanitize)

    # copy files
    for file in assignment.files:

        # if a directory, copy the entire dir
        if os.path.isdir(file):
            shutil.copytree(file, str(output_dir / os.path.basename(file)))
            
        else:
            # check that file is in subdir
            # TODO: convert to something other than assertion error
            assert str(assignment.master.parent) in os.path.abspath(file), \
                f"{file} is not in a subdirectory of the master notebook directory"
            file_path = pathlib.Path(file).resolve()
            rel_path = file_path.parent.relative_to(assignment.master.parent)
            os.makedirs(output_dir / rel_path, exist_ok=True)
            shutil.copy(file, str(output_dir / rel_path))


def write_output_directories(master_nb_path, result_dir, assignment):
    """
    """
    if assignment.is_rmd:
        nb = rmarkdown_converter.read_as_notebook(master_nb_path) # TODO: change arg name?
    else:
        nb = nbformat.read(master_nb_path, as_version=NB_VERSION)

    if assignment.lang is None:
        try:
            assignment.lang = get_notebook_language(nb)
        except KeyError:
            warnings.warn("Could not auto-parse kernelspec from notebook; assuming Python")
            assignment.lang = "python"

    tests_mgr = (RAssignmentTestsManager if assignment.is_r else AssignmentTestsManager)(assignment)
    nb_transformer = NotebookTransformer(assignment, tests_mgr)
    nb_transformer.transform_notebook(nb)

    # update assignment.tests["files"] for R notebooks
    assignment.tests["files"] |= assignment.is_r

    # force test files if a test URL prefix is provided
    if assignment.tests["url_prefix"]:
        assignment.tests["files"] = True

    # create directories
    autograder_dir = result_dir / 'autograder'
    student_dir = result_dir / 'student'
    shutil.rmtree(autograder_dir, ignore_errors=True)
    shutil.rmtree(student_dir, ignore_errors=True)
    os.makedirs(autograder_dir, exist_ok=True)
    os.makedirs(student_dir, exist_ok=True)

    # populate directories
    write_output_dir(nb_transformer, autograder_dir, assignment, False)
    write_output_dir(nb_transformer, student_dir, assignment, True)
