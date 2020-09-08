"""
Runs Otter on Gradescope with the configurations specified below
"""

import os
import subprocess

from otter.generate.run_autograder import main as run_autograder

config = {
    "score_threshold": None,
    "points_possible": None,
    "show_stdout_on_release": False,
    "show_hidden_tests_on_release": False,
    "seed": None,
    "grade_from_log": False,
    "serialized_variables": {},
    "public_multiplier": 0,
    "token": None,
    "course_id": 'None',
    "assignment_id": 'None',
    "filtering": True,
    "pagebreaks": True,
    "debug": False,
    "autograder_dir": '/autograder',
    "lang": 'python',
}

if __name__ == "__main__":
    run_autograder(config)