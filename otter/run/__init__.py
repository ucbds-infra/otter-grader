"""Non-containerized single notebook grading for Otter-Grader"""

import click
import json
import os
import pickle
import shutil
import tempfile
import zipfile

from .run_autograder import main as run_autograder

from ..cli import cli


def main(submission, autograder, output_dir, no_logo, debug):
    """
    Grades a single submission using the autograder configuration ``autograder`` without containrization

    Creates a temporary directory in the user's system and replicates grading container structure. Calls
    the autograder and loads the pickled results object. **Note:** This does not run any setup or 
    installation files, so the user's environment will need to have everything pre-installed.

    Args:
        submission (``str``): path to a submission to grade
        autograder (``str``): path to an Otter configuration zip file
        output_dir (``str``): directory at which to copy the results JSON file
        no_logo (``bool``): whether to suppress the Otter logo from being printed to stdout
        debug (``bool``); whether to run in debug mode (without ignoring errors)
        **kwargs: ignored kwargs (a remnant of how the argument parser is built)

    Returns:
        ``otter.test_files.GradingResults``: the grading results object
    """

    dp = tempfile.mkdtemp()

    try:
        ag_dir = os.path.join(dp, "autograder")

        for subdir in ["source", "submission", "results"]:
            path = os.path.join(ag_dir, subdir)
            os.makedirs(path, exist_ok=True)

        with open(os.path.join(ag_dir, "submission_metadata.json"), "w+") as f:
            json.dump({}, f)
        
        ag_zip = zipfile.ZipFile(autograder)
        ag_zip.extractall(os.path.join(ag_dir, "source"))
        ag_zip.close()

        shutil.copy(submission, os.path.join(ag_dir, "submission"))

        logo = not no_logo
        run_autograder(ag_dir, logo=logo, debug=debug)

        results_path = os.path.join(ag_dir, "results", "results.json")
        shutil.copy(results_path, output_dir)

        results_pkl_path = os.path.join(ag_dir, "results", "results.pkl")
        with open(results_pkl_path, "rb") as f:
            results = pickle.load(f)

    except:
        shutil.rmtree(dp)
        raise
    
    else:
        shutil.rmtree(dp)

    return results


@cli.command("run")
@click.argument("submission", help="Path to submission to be graded")
@click.option("-a", "--autograder", default="./autograder.zip", type=click.Path(exists=True, dir_okay=False), help="Path to autograder zip file")
@click.option("-o", "--output-dir", default="./", type=click.Path(exists=True, file_okay=False), help="Directory to which to write output")
@click.option("--no-logo", is_flag=True, help="Suppress Otter logo in stdout")
@click.option("--debug", is_flag=True, help="Do not ignore errors when running submission")
def run_cli(*args, **kwargs):
    """
    Run non-containerized Otter on a single submission.
    """
    return main(*args, **kwargs)
