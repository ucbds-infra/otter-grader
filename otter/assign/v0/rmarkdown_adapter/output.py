"""
Output writing for Otter Assign
"""

import os
import shutil
import pathlib
import warnings
import nbformat

from .notebook_transformer import transform_notebook
from .solutions import strip_solutions_and_output

from ..r_adapter.tests import remove_hidden_tests_from_dir
from ..tests import write_test

def write_autograder_dir(rmd_path, output_rmd_path, assignment):
    """
    Converts a master Rmd file to a solutions Rmd file and writes this file to the output directory,
    copying support files and writing tests as needed.

    Args:
        rmd_path (``pathlib.Path``): path to master Rmd file
        output_rmd_path (``pathlib.Path``): path to output Rmd file
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
    """
    with open(rmd_path) as f:
        rmd_string = f.read()

    if assignment.lang is None:
        assignment.lang = "r"

    output_dir = output_rmd_path.parent
    tests_dir = output_dir / 'tests'
    os.makedirs(tests_dir, exist_ok=True)

    requirements = assignment.requirements
    if requirements is None and os.path.isfile("requirements.R"):
        requirements = "requirements.R"
    if requirements:
        assert os.path.isfile(requirements), f"Requirements file {requirements} not found"
        assignment.requirements = requirements

    if assignment.requirements:
        shutil.copy(requirements, str(output_dir / 'requirements.R'))


    environment = assignment.environment
    if environment is None and os.path.isfile("environment.yml"):
        environment = "environment.yml"
    if environment:
        assert os.path.isfile(environment), f"Environment file {environment} not found"
        assignment.environment = environment

    if assignment.environment:
        shutil.copy(environment, str(output_dir / 'environment.yml'))

    transformed_rmd_string, test_files = transform_notebook(rmd_string, assignment)

    # write notebook
    with open(output_rmd_path, "w+") as f:
        f.write(transformed_rmd_string)

    # write tests
    test_ext =".R"
    for test_name, test_file in test_files.items():
        write_test({}, tests_dir / (test_name + test_ext), test_file, use_file=True)

    # copy files
    for file in assignment.files:

        # if a directory, copy the entire dir
        if os.path.isdir(file):
            shutil.copytree(file, str(output_dir / os.path.basename(file)))

        else:
            # check that file is in subdir
            assert os.path.abspath(rmd_path.parent) in os.path.abspath(file), \
                f"{file} is not in a subdirectory of the master notebook directory"
            file_path = pathlib.Path(file).resolve()
            rel_path = file_path.parent.relative_to(rmd_path.parent)
            os.makedirs(output_dir / rel_path, exist_ok=True)
            shutil.copy(file, str(output_dir / rel_path))

def write_student_dir(rmd_name, autograder_dir, student_dir, assignment):
    """
    Copies the autograder (solutions) directory and removes extraneous files, strips solutions from
    the Rmd file, and removes hidden tests from the tests directory.

    Args:
        rmd_name (``str``): the master Rmd file name
        autograder_dir (``pathlib.Path``): the path to the autograder directory
        student_dir (``pathlib.Path``): the path to the student directory
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
    """
    # copy autograder dir
    shutil.copytree(autograder_dir, student_dir)

    # remove requirements from student dir if present
    requirements = str(student_dir / 'requirements.R')
    if os.path.isfile(requirements):
        os.remove(requirements)

    # remove environment from student dir if present
    environment = str(student_dir / 'environment.yml')
    if os.path.isfile(environment):
        os.remove(environment)

    # strip solutions from student version
    student_rmd_path = student_dir / rmd_name
    with open(student_rmd_path) as f:
        # nb = nbformat.read(f, as_version=NB_VERSION)
        rmd_string = f.read()

    rmd_string = strip_solutions_and_output(rmd_string)

    with open(student_rmd_path, "w") as f:
        f.write(rmd_string)

    # remove hidden tests from student directory
    remove_hidden_tests_from_dir({}, student_dir / 'tests', assignment)

def write_output_directories(master_rmd_path, result_dir, assignment):
    """
    Converts a master Rmd file to an autograder and student directory based on configurations in 
    ``assignment``.

    Args:
        master_rmd_path (``pathlib.Path``): the master Rmd path
        result_dir (``pathlib.Path``): path to the result directory
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
    """
    # create directories
    autograder_dir = result_dir / 'autograder'
    student_dir = result_dir / 'student'
    shutil.rmtree(autograder_dir, ignore_errors=True)
    shutil.rmtree(student_dir, ignore_errors=True)
    os.makedirs(autograder_dir, exist_ok=True)

    # write autograder directory
    output_rmd_path = autograder_dir / master_rmd_path.name
    write_autograder_dir(master_rmd_path, output_rmd_path, assignment)

    # write student dir
    write_student_dir(master_rmd_path.name, autograder_dir, student_dir, assignment)
