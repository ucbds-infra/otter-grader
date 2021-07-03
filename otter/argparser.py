"""
Argument parser for Otter command-line tools
"""

import sys
import argparse

from textwrap import dedent

INVOKED_FROM_PYTHON = "__main__.py" in sys.argv[0]
PROG = ("otter", "python3 -m otter")[INVOKED_FROM_PYTHON]

def get_parser():
    """
    Creates and returns the argument parser for Otter

    Returns:
        ``argparse.ArgumentParser``: the argument parser for Otter command-line tools
    """

    parser = argparse.ArgumentParser(prog=PROG, description=dedent("""\
    Command-line utility for Otter-Grader, a Python-based autograder for Jupyter Notebooks, RMarkdown 
    files, and Python and R scripts that runs locally on the instructors machine. For more information,
    see https://otter-grader.readthedocs.io/
    """))
    parser.add_argument("--version", default=False, action="store_true", help="Show version information and exit")
    subparsers = parser.add_subparsers()


    ##### PARSER FOR otter assign #####
    assign_parser = subparsers.add_parser("assign", description="Create distribution versions of otter-assign-formatted notebook")
    assign_parser.add_argument("master", help="Notebook with solutions and tests.")
    assign_parser.add_argument("result", help="Directory containing the result.")
    assign_parser.add_argument("--no-run-tests", help="Don't run tests.", default=False, action="store_true")
    assign_parser.add_argument("--no-pdfs", help="Don't generate PDFs; overrides assignment config", default=False, action="store_true")
    assign_parser.add_argument("--username", default=None, help="Gradescope username for generating a token")
    assign_parser.add_argument("--password", default=None, help="Gradescope password for generating a token")
    assign_parser.add_argument("--debug", default=False, action="store_true", help="Do not ignore errors in running tests for debugging")

    assign_parser.set_defaults(func_str="assign.main")


    ##### PARSER FOR otter check #####
    check_parser = subparsers.add_parser("check", description="Checks Python file against tests")
    check_parser.add_argument("file", help="Python file to grade")
    check_parser.add_argument("-q", "--question", help="Grade a specific test")
    check_parser.add_argument("-t", "--tests-path", default="tests", help="Path to test files")
    check_parser.add_argument("--seed", type=int, default=None, help="A random seed to be executed before each cell")

    check_parser.set_defaults(func_str="check.main")


    ##### PARSER FOR otter export #####
    export_parser = subparsers.add_parser("export", description="Exports a Jupyter Notebook to PDF with optional filtering")
    export_parser.add_argument("source", help="Notebook to export")
    export_parser.add_argument("dest", nargs='?', default=None, help="Path to write PDF")
    export_parser.add_argument("--filtering", default=False, action="store_true", help="Whether the PDF should be filtered")
    export_parser.add_argument("--pagebreaks", default=False, action="store_true", help="Whether the PDF should have pagebreaks between questions")
    export_parser.add_argument("-s", "--save", default=False, action="store_true", help="Save intermediate file(s) as well")
    export_parser.add_argument("-e", "--exporter", default=None, choices=["latex", "html"], nargs="?", help="Type of PDF exporter to use")
    export_parser.add_argument("--debug", default=False, action="store_true", help="Export in debug mode")

    export_parser.set_defaults(func_str="export.main")


    ##### PARSER FOR otter generate #####
    generate_parser = subparsers.add_parser("generate", description="Generates zipfile to configure Gradescope autograder")
    generate_parser.add_argument("-t", "--tests-path", nargs='?', type=str, default="./tests/", help="Path to test files")
    generate_parser.add_argument("-o", "--output-path", nargs='?', type=str, default="./", help="Path to which to write zipfile")
    generate_parser.add_argument("-c", "--config", nargs='?', default=None, help="Path to otter configuration file; ./otter_config.json automatically checked")
    generate_parser.add_argument("-r", "--requirements", nargs='?', default=None, help="Path to requirements.txt file; ./requirements.txt automatically checked")
    generate_parser.add_argument("--overwrite-requirements", default=False, action="store_true", help="Overwrite (rather than append to) default requirements for Gradescope; ignored if no REQUIREMENTS argument")
    generate_parser.add_argument("-e", "--environment", nargs='?', default=None, help="Path to environment.yml file; ./environment.yml automatically checked (overwrite)")
    generate_parser.add_argument("-l", "--lang", default="python", choices=["python", "r"], type=str, help="Assignment programming language; defaults to Python")
    generate_parser.add_argument("--autograder-dir", nargs="?", default="/autograder", help="Root autograding directory inside grading container")
    generate_parser.add_argument("--username", default=None, help="Gradescope username for generating a token")
    generate_parser.add_argument("--password", default=None, help="Gradescope password for generating a token")
    generate_parser.add_argument("files", nargs='*', help="Other support files needed for grading (e.g. .py files, data files)")

    generate_parser.set_defaults(func_str="generate.main")


    ##### PARSER FOR otter grade #####
    grade_parser = subparsers.add_parser("grade", description="Grade assignments locally using Docker containers")

    # necessary path arguments
    grade_parser.add_argument("-p", "--path", type=str, default="./", help="Path to directory of submissions")
    grade_parser.add_argument("-a", "--autograder", type=str, default="./autograder.zip", help="Path to autograder zip file")
    grade_parser.add_argument("-o", "--output-dir", type=str, default="./", help="Directory to which to write output")

    # metadata parser arguments
    grade_parser.add_argument("-g", "--gradescope", action="store_true", default=False, help="Flag for Gradescope export")
    grade_parser.add_argument("-c", "--canvas", action="store_true", default=False, help="Flag for Canvas export")
    grade_parser.add_argument("-j", "--json", default=False, help="Flag for path to JSON metadata")
    grade_parser.add_argument("-y", "--yaml", default=False, help="Flag for path to YAML metadata")

    # submission format arguments
    grade_parser.add_argument("-s", "--scripts", action="store_true", default=False, help="Flag to incidicate grading Python scripts")
    grade_parser.add_argument("-z", "--zips", action="store_true", default=False, help="Whether submissions are zip files from Notebook.export")

    # PDF export options
    grade_parser.add_argument("--pdfs", default=False, action="store_true", help="Whether to copy notebook PDFs out of containers")

    # other settings and optional arguments
    grade_parser.add_argument("-v", "--verbose", action="store_true", help="Flag for verbose output")
    grade_parser.add_argument("--containers", type=int, help="Specify number of containers to run in parallel")
    grade_parser.add_argument("--image", default="ucbdsinfra/otter-grader", help="Custom docker image to run on")
    grade_parser.add_argument("--no-kill", action="store_true", default=False, help="Do not kill containers after grading")
    grade_parser.add_argument("--debug", action="store_true", default=False, help="Print stdout/stderr from grading for debugging")

    grade_parser.add_argument("--prune", action="store_true", default=False, help="Prune all of Otter's grading images")
    grade_parser.add_argument("-f", "--force", action="store_true", default=False, help="Force action (don't ask for confirmation)")

    grade_parser.set_defaults(func_str="grade.main")


    ###### PARSER FOR otter run #####
    run_parser = subparsers.add_parser("run", description="Run non-containerized Otter on a single submission") # TODO
    run_parser.add_argument("submission", help="Path to submission to be graded")
    run_parser.add_argument("-a", "--autograder", default="./autograder.zip", help="Path to autograder zip file")
    run_parser.add_argument("-o", "--output-dir", default="./", help="Directory to which to write output")
    run_parser.add_argument("--no-logo", action="store_true", default=False, help="Suppress Otter logo in stdout")
    run_parser.add_argument("--debug", default=False, action="store_true", help="Do not ignore errors when running submission")

    run_parser.set_defaults(func_str="run.main")


    return parser
