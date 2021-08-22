"""A programmatic API for using Otter-Grader"""

__all__ = ["export_notebook", "grade_submission"]

import os
import sys
import shutil
import tempfile

from contextlib import redirect_stdout

try:
    from contextlib import nullcontext
except ImportError:
    from .utils import nullcontext  # nullcontext is new in Python 3.7

from .export import export_notebook
from .run import main as run_grader


def grade_submission(ag_path, submission_path, quiet=False, debug=False):
    """
    Runs non-containerized grading on a single submission at ``submission_path`` using the autograder 
    configuration file at ``ag_path``. 
    
    Creates a temporary grading directory using the ``tempfile`` library and grades the submission 
    by replicating the autograder tree structure in that folder and running the autograder there. Does
    not run environment setup files (e.g. ``setup.sh``) or install requirements, so any requirements 
    should be available in the environment being used for grading. 
    
    Print statements executed during grading can be suppressed with ``quiet``.

    Args:
        ag_path (``str``): path to autograder zip file
        submission_path (``str``): path to submission file
        quiet (``bool``, optional): whether to suppress print statements during grading; default 
            ``False``
        debug (``bool``, optional): whether to run the submission in debug mode (without ignoring
            errors)

    Returns:
        ``otter.test_files.GradingResults``: the results object produced during the grading of the
            submission.
    """

    dp = tempfile.mkdtemp()

    if quiet:
        f = open(os.devnull, "w")
        cm = redirect_stdout(f)
    else:
        cm = nullcontext()

    # TODO: is the output_dir argument of run_grader necessary here?
    with cm:
        results = run_grader(submission_path, ag_path, dp, True, debug)

    if quiet:
        f.close()

    shutil.rmtree(dp)

    return results
