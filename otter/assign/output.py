"""
Output writing for Otter Assign
"""

import os
import shutil
import pathlib
import warnings
import nbformat

from .constants import NB_VERSION
from .notebook_transformer import transform_notebook
from .plugins import replace_plugins_with_calls
from .solutions import strip_ignored_lines, strip_solutions_and_output
from .tests import write_test
from .utils import patch_copytree

def write_autograder_dir(nb_path, output_nb_path, assignment):
    """
    Converts a master notebook to a solutions notebook and writes this notebook to the output directory,
    copying support files and writing tests as needed.

    Args:
        nb_path (``pathlib.Path``): path to master notebook
        output_nb_path (``pathlib.Path``): path to output file
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
    """
    with open(nb_path) as f:
        nb = nbformat.read(f, as_version=NB_VERSION)

    if assignment.lang is None:
        try:
            lang = nb["metadata"]["kernelspec"]["language"].lower()
            assignment.lang = lang
        except KeyError:
            warnings.warn("Could not auto-parse kernelspec from notebook; assuming Python")
            assignment.lang = "python"

    output_dir = output_nb_path.parent
    tests_dir = output_dir / 'tests'
    os.makedirs(tests_dir, exist_ok=True)

    transformed_nb, test_files = transform_notebook(nb, assignment)

    # replace plugins
    transformed_nb = replace_plugins_with_calls(transformed_nb)

    if assignment.requirements:
        output_fn = ("requirements.txt", "requirements.R")[assignment.is_r]
        if isinstance(assignment.requirements, list):
            with open(str(output_dir / output_fn), "w+") as f:
                f.write("\n".join(assignment.requirements))
            assignment.requirements = str(output_dir / output_fn)
        else:
            shutil.copy(assignment.requirements, str(output_dir / output_fn))
    
    # strip out ignored lines
    transformed_nb = strip_ignored_lines(transformed_nb)

    # write notebook
    # with open(output_nb_path) as f:
    # nbformat.write(transformed_nb, )
    nbformat.write(transformed_nb, str(output_nb_path))

    # write tests
    test_ext = (".R", ".py")[assignment.is_python]
    for test_name, test_file in test_files.items():
        write_test(tests_dir / (test_name + test_ext), test_file)

    # copy files
    for file in assignment.files:

        # if a directory, copy the entire dir
        if os.path.isdir(file):
            shutil.copytree(file, str(output_dir / os.path.basename(file)))
            
        else:
            # check that file is in subdir
            assert os.path.abspath(nb_path.parent) in os.path.abspath(file), \
                f"{file} is not in a subdirectory of the master notebook directory"
            file_path = pathlib.Path(file).resolve()
            rel_path = file_path.parent.relative_to(nb_path.parent)
            os.makedirs(output_dir / rel_path, exist_ok=True)
            shutil.copy(file, str(output_dir / rel_path))

def write_student_dir(nb_name, autograder_dir, student_dir, assignment):
    """
    Copies the autograder (solutions) directory and removes extraneous files, strips solutions from
    the notebook, and removes hidden tests from the tests directory.

    Args:
        nb_name (``str``): the master notebook name
        autograder_dir (``pathlib.Path``): the path to the autograder directory
        student_dir (``pathlib.Path``): the path to the student directory
        assignment (``otter.assign.assignment.Assignment``): the assignment configurations
    """
    if assignment.is_r:
        from .r_adapter.tests import remove_hidden_tests_from_dir
    else:
        from .tests import remove_hidden_tests_from_dir

    # copy autograder dir
    with patch_copytree():
        shutil.copytree(autograder_dir, student_dir, copy_function=shutil.copy)

    # remove requirements from student dir if present
    output_fn = ("requirements.txt", "requirements.R")[assignment.is_r]
    requirements = str(student_dir / output_fn)
    if os.path.isfile(requirements):
        os.remove(requirements)

    # strip solutions from student version
    student_nb_path = student_dir / nb_name
    with open(student_nb_path) as f:
        nb = nbformat.read(f, as_version=NB_VERSION)

    nb = strip_solutions_and_output(nb)

    with open(student_nb_path, "w") as f:
        nbformat.write(nb, f)

    # remove hidden tests from student directory
    remove_hidden_tests_from_dir(student_dir / 'tests', assignment)

def write_output_directories(master_nb_path, result_dir, assignment):
    """
    Converts a master notebook to an autograder and student directory based on configurations in 
    ``assignment``.

    Args:
        master_nb_path (``nbformat.NotebookNode``): the master notebook path
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
    output_nb_path = autograder_dir / master_nb_path.name
    write_autograder_dir(master_nb_path, output_nb_path, assignment)

    # write student dir
    write_student_dir(master_nb_path.name, autograder_dir, student_dir, assignment)
