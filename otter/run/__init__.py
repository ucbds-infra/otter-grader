"""Non-containerized single notebook grading for Otter-Grader"""

import json
import os
import pickle
import shutil
import tempfile
import zipfile

from .run_autograder import main as run_autograder


def main(submission, *, autograder="./autograder.zip", output_dir="./", no_logo=False, debug=False):
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

    finally:
        shutil.rmtree(dp)

    return results
