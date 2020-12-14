"""
"""

import os
import shutil
import tempfile

from contextlib import redirect_stdout

from . import main as run_grader
from ..argparser import get_parser

PARSER = get_parser()
ARGS_STARTER = ["run"]

def grade_submission(ag_path, submission_path):
    dp = tempfile.mkdtemp()

    args_list = ARGS_STARTER.copy()
    args_list.extend([
        "-a", ag_path,
        "-o", dp,
        submission_path,
    ])

    args = PARSER.parse_args(args_list)

    with open(os.devnull, "w") as f, redirect_stdout(f):
        results = run_grader(args)

    shutil.rmtree(dp)

    return results
