"""Assignment creation tool for Otter-Grader"""

import os
import pathlib
import warnings

from .assignment import Assignment
from .output import write_output_directories
from .utils import run_tests, write_otter_config_file, run_generate_autograder

from ..export import export_notebook, WkhtmltopdfNotFoundError
from ..plugins import PluginCollection
from ..utils import chdir, get_relpath, knit_rmd_file, loggers


LOGGER = loggers.get_logger(__name__)


def main(
    master,
    result,
    *,
    no_pdfs=False,
    no_run_tests=False,
    username=None,
    password=None, 
    debug=False,
):
    """
    Runs Otter Assign on a master notebook.

    Args:
        master (``str``): path to master notebook
        result (``str``): path to result directory
        no_pdfs (``bool``): whether to ignore any configurations indicating PDF generation for this run
        no_run_tests (``bool``): prevents Otter tests from being automatically run on the solutions 
            notebook
        username (``str``): a username for Gradescope for generating a token
        password (``str``): a password for Gradescope for generating a token
        debug (``bool``): whether to run in debug mode (without ignoring errors during testing)
    """
    LOGGER.debug(f"User-specified master path: {master}")
    LOGGER.debug(f"User-specified result path: {result}")
    master, result = pathlib.Path(os.path.abspath(master)), pathlib.Path(os.path.abspath(result))

    assignment = Assignment()

    result = get_relpath(master.parent, result)

    assignment.master, assignment.result = master, result
    LOGGER.debug(f"Normalized master path: {master}")
    LOGGER.debug(f"Normalized result path: {result}")

    with chdir(master.parent):
        LOGGER.info("Generating views")
        write_output_directories(assignment)

        # update seed variables
        if assignment.seed.variable:
            LOGGER.debug("Processing seed dict")
            assignment.generate.seed = assignment.seed.autograder_value
            assignment.generate.seed_variable = assignment.seed.variable
            LOGGER.debug("Added seed information to assignment.generate")

        # check that we have a seed if needed
        if assignment.seed_required:
            LOGGER.debug("Assignment seed is required")
            if not isinstance(assignment.generate.seed, int):
                raise RuntimeError("Seeding cell found but no or invalid seed provided")

        plugins, pc = assignment.plugins, None
        if plugins:
            LOGGER.debug("Processing plugins")
            pc = PluginCollection(plugins, "", {})
            pc.run("during_assign", assignment)

            LOGGER.debug("Adding plugin configurations to Otter Generate configuration")
            assignment.generate.plugins = assignment.generate.plugins + plugins

        LOGGER.info("Generating autograder zipfile")
        run_generate_autograder(assignment, username, password, plugin_collection=pc)

        # generate PDF of solutions
        if assignment.solutions_pdf and not no_pdfs:
            LOGGER.info("Generating solutions PDF")
            filtering = assignment.solutions_pdf == 'filtered'

            src = os.path.abspath(str(assignment.get_ag_path(master.name)))
            dst = os.path.abspath(str(assignment.get_ag_path(master.stem + '-sol.pdf')))

            if not assignment.is_rmd:
                LOGGER.debug(f"Exporting {src} as notebook to {dst}")
                try:
                    LOGGER.debug("Attempting PDF via HTML export")
                    export_notebook(
                        src,
                        dest=dst,
                        filtering=filtering,
                        pagebreaks=filtering,
                        exporter_type="html",
                    )
                    LOGGER.debug("PDF via HTML export successful")

                except WkhtmltopdfNotFoundError:
                    LOGGER.debug("PDF via HTML export failed; attempting PDF via LaTeX export")
                    export_notebook(
                        src,
                        dest=dst,
                        filtering=filtering,
                        pagebreaks=filtering,
                    )
                    LOGGER.debug("PDF via LaTeX export successful")

            else:
                LOGGER.debug(f"Knitting {src} to {dst}")
                if filtering:
                    raise ValueError("Filtering is not supported with RMarkdown assignments")

                knit_rmd_file(src, dst)

        # generate a tempalte PDF for Gradescope
        if assignment.template_pdf and not no_pdfs:
            LOGGER.info("Generating template PDF")

            src = os.path.abspath(str(assignment.get_ag_path( master.name)))
            dst = os.path.abspath(str(assignment.get_ag_path(master.stem + '-template.pdf')))

            if not assignment.is_rmd:
                LOGGER.debug("Attempting PDF via LaTeX export")
                export_notebook(
                    src,
                    dest=dst, 
                    filtering=True, 
                    pagebreaks=True, 
                    exporter_type="latex",
                )
                LOGGER.debug("PDF via LaTeX export successful")

            else:
                raise ValueError(f"Filtering is not supported with RMarkdown assignments; use " + \
                    "solutions_pdf to generate a Gradescope template instead.")

        # generate the .otter file if needed
        if not assignment.is_rmd and assignment.save_environment:
            LOGGER.debug("Processing environment serialization configuration")
            if assignment.is_r:
                warnings.warn(
                    "Otter Service and serialized environments are unsupported with R, "
                    "configurations ignored")
            else:
                write_otter_config_file(assignment)

        # run tests on autograder notebook
        if assignment.run_tests and not no_run_tests:
            LOGGER.info("Running tests against the solutions notebook")

            run_tests(assignment, debug=debug)

            LOGGER.info("All autograder tests passed.")

        else:
            LOGGER.info("Skipping tests")
