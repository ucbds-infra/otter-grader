"""
Otter Assign command-line utility
"""

import os
import pathlib
import warnings

from .assignment import Assignment
from .utils import run_tests, write_otter_config_file, run_generate_autograder

from ..export import export_notebook
from ..export.exporters import WkhtmltopdfNotFoundError
from ..plugins import PluginCollection
from ..utils import get_relpath, block_print

def main(master, result, no_pdfs, no_run_tests, username, password, debug, **kwargs):
    """
    Runs Otter Assign on a master notebook
    
    Args:
        master (``str``): path to master notebook
        result (``str``): path to result directory
        no_pdfs (``bool``): whether to ignore any configurations indicating PDF generation for this run
        no_run_tests (``bool``): prevents Otter tests from being automatically run on the solutions 
            notebook
        username (``str``): a username for Gradescope for generating a token
        password (``str``): a password for Gradescope for generating a token
        debug (``bool``): whether to run in debug mode (without ignoring errors during testing)
        **kwargs: ignored kwargs (a remnant of how the argument parser is built)
    """
    master, result = pathlib.Path(os.path.abspath(master)), pathlib.Path(os.path.abspath(result))
    print("Generating views...")

    assignment = Assignment()

    # # check language
    # if lang is not None:
    #     lang = lang.lower()
    #     assert lang in ["r", "python"], f"Language {lang} is not valid"
    #     assignment.lang = lang
    
    # TODO: update this condition
    if True:
        result = get_relpath(master.parent, result)
        orig_dir = os.getcwd()
        os.chdir(master.parent)
        # master = pathlib.Path(master.name)
    
    assignment.master, assignment.result = master, result
    # assignment.files = files

    if assignment.is_rmd:
        from .rmarkdown_adapter.output import write_output_directories
    else:
        from .output import write_output_directories

    # # update requirements
    # requirements = requirements
    # if requirements is None and os.path.isfile("requirements.txt"):
    #     requirements = "requirements.txt"
    # if requirements:
    #     assert os.path.isfile(requirements), f"Requirements file {requirements} not found"
    # assignment.requirements = requirements
    
    try:
        write_output_directories(master, result, assignment)

        # check that we have a seed if needed
        if assignment.seed_required:
            generate_args = assignment.generate
            if generate_args is True:
                generate_args = {'seed': None}
            assert not generate_args or generate_args.get('seed', None) is not None or \
                not assignment.is_python, "Seeding cell found but no seed provided"

        plugins = assignment.plugins
        if plugins:
            pc = PluginCollection(plugins, "", {})
            pc.run("during_assign", assignment)
            if assignment.generate is True:
                assignment.generate = {"plugins": []}
            if assignment.generate is not False:
                if not assignment.generate.get("plugins"):
                    assignment.generate["plugins"] = []
                assignment.generate["plugins"].extend(plugins)
        else:
            pc = None
        
        # generate PDF of solutions
        if assignment.solutions_pdf and not assignment.is_rmd and not no_pdfs:
            print("Generating solutions PDF...")
            filtering = assignment.solutions_pdf == 'filtered'

            try:
                export_notebook(
                    str(result / 'autograder' / master.name),
                    dest=str(result / 'autograder' / (master.stem + '-sol.pdf')),
                    filtering=filtering,
                    pagebreaks=filtering,
                    exporter_type="html",
                )
            except WkhtmltopdfNotFoundError:
                export_notebook(
                    str(result / 'autograder' / master.name),
                    dest=str(result / 'autograder' / (master.stem + '-sol.pdf')),
                    filtering=filtering,
                    pagebreaks=filtering,
                )

        # generate a tempalte PDF for Gradescope
        if not assignment.is_rmd and assignment.template_pdf and not no_pdfs:
            print("Generating template PDF...")
            export_notebook(
                str(result / 'autograder' / master.name),
                dest=str(result / 'autograder' / (master.stem + '-template.pdf')), 
                filtering=True, 
                pagebreaks=True, 
                exporter_type="latex",
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
            run_generate_autograder(result, assignment, username, password)

        # run tests on autograder notebook
        if assignment.run_tests and not no_run_tests and assignment.is_python:
            print("Running tests...")
            # with block_print():
            if isinstance(assignment.generate, bool):
                seed = None
            else:
                seed = assignment.generate.get('seed', None)
            run_tests(result / 'autograder' / master.name, debug=debug, seed=seed, plugin_collection=pc)
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
