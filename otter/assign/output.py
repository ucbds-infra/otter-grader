import os
import shutil
import pathlib
import nbformat

from .defaults import NB_VERSION
from .notebook_transformer import transform_notebook
from .solutions import strip_solutions_and_output
from .tests import write_test, remove_hidden_tests_from_dir

def write_autograder_dir(nb_path, output_nb_path, assignment, args):
    """
    """
    with open(nb_path) as f:
        nb = nbformat.read(f, as_version=NB_VERSION)

    output_dir = output_nb_path.parent
    tests_dir = output_dir / 'tests'
    os.makedirs(tests_dir, exist_ok=True)

    requirements = assignment.requirements or args.requirements
    if os.path.isfile(requirements):
        shutil.copy(requirements, str(output_dir / 'requirements.txt'))

    transformed_nb, test_files = transform_notebook(nb, assignment, args)

    # write notebook
    with open(output_nb_path) as f:
        nbformat.write(transformed_nb, f)

    # write tests
    for test_name, test_file in test_files.items():
        write_test(tests_dir / (test_name + ".py"), test_file)

    # copy files
    for file in assignment.files or args.files:

        # if a directory, copy the entire dir
        if os.path.isdir(file):
            shutil.copytree(file, str(output_dir / os.path.basename(file)))
            
        else:
            # check that file is in subdir
            assert os.path.abspath(nb_path.parent) in os.path.abspath(file), \
                f"{file} is not in a subdirectory of the master notebook directory"
            file_path = pathlib.Path(file)
            rel_path = file_path.parent.relative_to(nb_path.parent)
            os.makedirs(output_dir / rel_path, exist_ok=True)
            shutil.copy(file, str(output_dir / rel_path))

def write_student_dir(nb_name, autograder_dir, student_dir, assignment, args):
    """
    """
    # copy autograder dir
    shutil.copytree(autograder_dir, student_dir)

    # remove requirements from student dir if present
    requirements = assignment.requirements or args.requirements
    requirements = str(student_dir / os.path.split(requirements)[1])
    if os.path.isfile(requirements):
        os.remove(requirements)

    # strip solutions from student version
    student_nb_path = student_dir / nb_name
    with open(student_nb_path) as f:
        nb = nbformat.read(f, as_version=NB_VERSION)

    nb = strip_solutions_and_output(nb)

    with open(student_nb_path) as f:
        nbformat.write(nb, f)

    # remove hidden tests from student directory
    remove_hidden_tests_from_dir(student_dir / 'tests')

def write_output_directories(master_nb_path, result_dir, assignment, args):
    """Generate student and autograder views.

    Args:
        master_nb (``nbformat.NotebookNode``): the master notebook
        result_dir (``pathlib.Path``): path to the result directory
        args (``argparse.Namespace``): parsed command line arguments
    """
    # create directories
    autograder_dir = result_dir / 'autograder'
    student_dir = result_dir / 'student'
    shutil.rmtree(autograder_dir, ignore_errors=True)
    shutil.rmtree(student_dir, ignore_errors=True)
    os.makedirs(autograder_dir, exist_ok=True)

    # write autograder directory
    output_nb_path = autograder_dir / master_nb_path.name
    write_autograder_dir(master_nb_path, output_nb_path, assignment, args)

    # write student dir
    write_student_dir(master_nb_path.name, autograder_dir, student_dir, assignment, args)
