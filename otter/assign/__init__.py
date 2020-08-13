"""
Otter Assign command-line utility
"""

import os
import pathlib
import warnings
# import nb2pdf

from .assignment import Assignment
from .utils import run_tests, write_otter_config_file, run_generate_autograder

# from .. import _WINDOWS
from ..export import export_notebook
from ..utils import get_relpath, block_print

# for now can't use nb2pdf on Windows b/c of pyppeteer - this may be due to my
# local install, requires further debugging
# TO_PDF_FN = (nb2pdf.convert, export_notebook)[_WINDOWS]

def main(args):
    """
    Runs Otter Assign
    
    Args:
        ``argparse.Namespace``: parsed command line arguments
    """
    master, result = pathlib.Path(args.master), pathlib.Path(args.result)
    print("Generating views...")

    assignment = Assignment()

    # check language
    if args.lang is not None:
        args.lang = args.lang.lower()
        assert args.lang in ["r", "python"], f"Language {args.lang} is not valid"
        assignment.lang = args.lang
    
    # TODO: update this condition
    if True:
        result = get_relpath(master.parent, result)
        orig_dir = os.getcwd()
        os.chdir(master.parent)
        master = pathlib.Path(master.name)
    
    assignment.master, assignment.result = master, result

    if assignment.is_rmd:
        from .rmarkdown_adapter.output import write_output_directories
    else:
        from .output import write_output_directories
    
    try:
        write_output_directories(master, result, assignment, args)

        # check that we have a seed if needed
        if assignment.seed_required:
            generate_args = assignment.generate
            if generate_args is True:
                generate_args = {'seed': None}
            assert not generate_args or generate_args.get('seed', None) is not None or \
                not assignment.is_python, "Seeding cell found but no seed provided"
        
        # generate PDF of solutions with nb2pdf -- DEPRECATED
        if assignment.solutions_pdf:
            # print("Generating solutions PDF...")
            # filtering = assignment.solutions_pdf == 'filtered'
            # TO_PDF_FN(
            #     str(result / 'autograder' / master.name),
            #     dest=str(result / 'autograder' / (master.stem + '-sol.pdf')),
            #     filtering=filtering
            # )
            warnings.warn("The solutions_pdf configuration is deprecated and will be ignored")

        # generate a tempalte PDF for Gradescope
        if not assignment.is_rmd and assignment.template_pdf:
            print("Generating template PDF...")
            export_notebook(
                str(result / 'autograder' / master.name),
                dest=str(result / 'autograder' / (master.stem + '-template.pdf')), 
                filtering=True, 
                pagebreaks=True, 
                exporter_type="latex"
            )

        # generate the .otter file if needed
        if not assignment.is_rmd and assignment.service or assignment.save_environment:
            if assignment.is_r:
                warnings.warn(
                    "Otter Service and serialized environments are unsupported with R, "
                    "configurations ignored"
                )
            else:
                write_otter_config_file(master, result, assignment)

        # generate Gradescope autograder zipfile
        if assignment.generate:
            # TODO: move this to another function
            print("Generating autograder zipfile...")
            run_generate_autograder(result, assignment, args)

        # run tests on autograder notebook
        if assignment.run_tests and not args.no_run_tests and assignment.is_python:
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
