"""Non-containerized single notebook grading for Otter-Grader"""

import dill
import json
import os
import pathlib
import shutil
import tempfile
import zipfile

from typing import Optional

from .run_autograder import AutograderConfig, capture_run_output, main as run_autograder_main
from ..test_files import GradingResults


__all__ = ["AutograderConfig", "capture_run_output", "main"]


def main(
    submission: str,
    *,
    autograder: str = "./autograder.zip",
    output_dir: str = "./",
    no_logo: bool = False,
    debug: bool = False,
    extra_submission_files: Optional[list[str]] = None,
) -> GradingResults:
    """
    Grades a single submission using the autograder configuration ``autograder`` without
    containerization.

    Creates a temporary directory in the user's system and replicates grading container structure.
    Calls the autograder and loads the pickled results object. **Note:** This does not run any setup
    or installation files, so the user's environment will need to have everything pre-installed.

    Args:
        submission (``str``): path to a submission to grade
        autograder (``str``): path to an Otter configuration zip file
        output_dir (``str | None``): directory at which to copy the results JSON file; if ``None``,
            the results JSON file is not copied
        no_logo (``bool``): whether to suppress the Otter logo from being printed to stdout
        debug (``bool``); whether to run in debug mode (without ignoring errors)
        extra_submission_files (``list[str] | None``): extra files to copy into the submission
            directory; this should really only be used internally by Otter, so use at your own risk

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

        if os.path.splitext(submission)[1] == ".zip":
            subm_zip = zipfile.ZipFile(submission)
            subm_zip.extractall(os.path.join(ag_dir, "submission"))
            subm_zip.close()

        else:
            shutil.copy(submission, os.path.join(ag_dir, "submission"))

        for file in extra_submission_files or []:
            fp = pathlib.Path(os.path.join(ag_dir, file))
            # create any intermediate directories before copying the file
            fp.parents[0].mkdir(parents=True, exist_ok=True)
            shutil.copy(file, os.path.join(ag_dir, "submission", file))

        logo = not no_logo
        run_autograder_main(ag_dir, logo=logo, debug=debug, otter_run=True)

        results_path = os.path.join(ag_dir, "results", "results.json")
        if output_dir:
            shutil.copy(results_path, output_dir)

        results_pkl_path = os.path.join(ag_dir, "results", "results.pkl")
        with open(results_pkl_path, "rb") as f:
            results = dill.load(f)

    finally:
        shutil.rmtree(dp)

    return results
