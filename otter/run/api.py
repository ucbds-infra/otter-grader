"""
"""

import os
import sys
import shutil
import tempfile

from contextlib import redirect_stdout, nullcontext

from . import main as run_grader
from ..argparser import get_parser

PARSER = get_parser()
ARGS_STARTER = ["run"]

def grade_submission(ag_path, submission_path, quiet=False):
    """
    """

    dp = tempfile.mkdtemp()

    args_list = ARGS_STARTER.copy()
    args_list.extend([
        "-a", ag_path,
        "-o", dp,
        submission_path,
        "--no-logo"
    ])

    args = PARSER.parse_args(args_list)

    if quiet:
        f = open(os.devnull, "w")
        cm = redirect_stdout(f)
    else:
        cm = nullcontext()
        
    with cm:
        results = run_grader(args)

    if quiet:
        f.close()

    shutil.rmtree(dp)

    return results
