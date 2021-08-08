"""
Argument parser for Otter command-line tools
"""

import click
import sys

from textwrap import dedent


INVOKED_FROM_PYTHON = "__main__.py" in sys.argv[0]
PROG = ("otter", "python3 -m otter")[INVOKED_FROM_PYTHON]


@click.group()
def cli():
    pass


from .assign import assign_cli
from .check import check_cli
from .export import export_cli
from .generate import generate_cli
from .grade import grade_cli

# def get_parser():
#     """
#     Creates and returns the argument parser for Otter

#     Returns:
#         ``argparse.ArgumentParser``: the argument parser for Otter command-line tools
#     """

#     parser = argparse.ArgumentParser(prog=PROG, description=dedent("""\
#     Command-line utility for Otter-Grader, a Python-based autograder for Jupyter Notebooks, RMarkdown 
#     files, and Python and R scripts that runs locally on the instructors machine. For more information,
#     see https://otter-grader.readthedocs.io/
#     """))
#     parser.add_argument("--version", default=False, action="store_true", help="Show version information and exit")
#     subparsers = parser.add_subparsers()



#     ###### PARSER FOR otter run #####
#     run_parser = subparsers.add_parser("run", description="Run non-containerized Otter on a single submission") # TODO
#     run_parser.add_argument("submission", help="Path to submission to be graded")
#     run_parser.add_argument("-a", "--autograder", default="./autograder.zip", help="Path to autograder zip file")
#     run_parser.add_argument("-o", "--output-dir", default="./", help="Directory to which to write output")
#     run_parser.add_argument("--no-logo", action="store_true", default=False, help="Suppress Otter logo in stdout")
#     run_parser.add_argument("--debug", default=False, action="store_true", help="Do not ignore errors when running submission")

#     run_parser.set_defaults(func_str="run.main")


#     return parser
