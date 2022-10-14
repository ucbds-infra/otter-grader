"""Non-containerized single notebook grading for Otter-Grader"""

import json
import os
import shutil
import tempfile
import zipfile

from .run_autograder import main as run_autograder_main

from ..utils import import_or_raise


def main(submission, *, autograder="./autograder.zip", output_dir="./", no_logo=False, debug=False):
    """
    Grades a single submission using the autograder configuration ``autograder`` without
    containerization.

    Creates a temporary directory in the user's system and replicates grading container structure.
    Calls the autograder and loads the pickled results object. **Note:** This does not run any setup
    or installation files, so the user's environment will need to have everything pre-installed.

    Args:
        submission (``str``): path to a submission to grade
        autograder (``str``): path to an Otter configuration zip file
        output_dir (``str``): directory at which to copy the results JSON file
        no_logo (``bool``): whether to suppress the Otter logo from being printed to stdout
        debug (``bool``); whether to run in debug mode (without ignoring errors)

    Returns:
        ``otter.test_files.GradingResults``: the grading results object
    """
    dill = import_or_raise("dill")
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

        if os.path.splitext(submission)[1] == ".zip":
            subm_zip = zipfile.ZipFile(submission)
            subm_zip.extractall(os.path.join(ag_dir, "submission"))
            subm_zip.close()

        else:
            shutil.copy(submission, os.path.join(ag_dir, "submission"))

        logo = not no_logo
        run_autograder_main(ag_dir, logo=logo, debug=debug)

        results_path = os.path.join(ag_dir, "results", "results.json")
        shutil.copy(results_path, output_dir)

        results_pkl_path = os.path.join(ag_dir, "results", "results.pkl")
        with open(results_pkl_path, "rb") as f:
            results = dill.load(f)

    finally:
        shutil.rmtree(dp)

    return results
