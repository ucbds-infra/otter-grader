"""
Argument parser for Otter command-line tools
"""

import click

from .version import print_version_info


@click.group()
@click.option("--version", is_flag=True, help="Show the version and exit")
def cli(version):
    """
    Command-line utility for Otter-Grader, a Python-based autograder for Jupyter Notebooks, 
    RMarkdown files, and Python and R scripts. For more information, see 
    https://otter-grader.readthedocs.io/.
    """
    if version:
        print_version_info(logo=True)
        return


from .assign import assign_cli
from .check import check_cli
from .export import export_cli
from .generate import generate_cli
from .grade import grade_cli
from .run import run_cli
