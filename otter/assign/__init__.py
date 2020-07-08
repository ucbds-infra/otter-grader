########################
##### Otter Assign #####
########################

import os
import pathlib
import nb2pdf

from .assignment import Assignment
from .output import write_output_directories
from .utils import run_tests, write_otter_config_file, run_generate_autograder

from ..export import export_notebook
from ..utils import get_relpath, block_print

def main(args):
    """
    Runs Otter Assign
    
    Args:
        ``argparse.Namespace``: parsed command line arguments
    """
    master, result = pathlib.Path(args.master), pathlib.Path(args.result)
    print("Generating views...")

    assignment = Assignment()
    
    # TODO: update this condition
    if True:
        result = get_relpath(master.parent, result)
        orig_dir = os.getcwd()
        os.chdir(master.parent)
        master = pathlib.Path(master.name)
    
    try:
        write_output_directories(master, result, assignment, args)

        # check that we have a seed if needed
        if assignment.seed_required:
            assert not assignment.generate or assignment.generate.get('seed', None) is not None, \
                "Seeding cell found but no seed provided"
        
        # generate PDF of solutions with nb2pdf
        if assignment.solutions_pdf:
            print("Generating solutions PDF...")
            filtering = assignment.solutions_pdf == 'filtered'
            nb2pdf.convert(
                str(result / 'autograder' / master.name),
                dest=str(result / 'autograder' / (master.stem + '-sol.pdf')),
                filtering=filtering
            )

        # generate a tempalte PDF for Gradescope
        if assignment.template_pdf:
            print("Generating template PDF...")
            export_notebook(
                str(result / 'autograder' / master.name),
                dest=str(result / 'autograder' / (master.stem + '-template.pdf')), 
                filtering=True, 
                pagebreaks=True
            )

        # generate the .otter file if needed
        if assignment.service or assignment.save_environment:
            write_otter_config_file(master, result, assignment)

        # generate Gradescope autograder zipfile
        if assignment.generate:
            # TODO: move this to another function
            print("Generating autograder zipfile...")
            run_generate_autograder(result, assignment, args)

        # run tests on autograder notebook
        if assignment.run_tests and not args.no_run_tests:
            print("Running tests...")
            with block_print():
                if isinstance(assignment.generate, bool):
                    seed = None
                else:
                    seed = assignment.generate.get('seed', None)
                run_tests(result / 'autograder' / master.name, debug=args.debug, seed=seed)
            print("All tests passed!")
    
    # for tests
    except:
        # TODO: change this condition
        if True:
            os.chdir(orig_dir)

        raise

    else:
        # TODO: change this condition
        if True:
            os.chdir(orig_dir)
