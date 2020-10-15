"""
Runs Otter on Gradescope with the configurations specified below
"""

import os
import subprocess

from otter.generate.run_autograder import main as run_autograder

# config = {
#     "score_threshold": ,
#     "points_possible": ,
#     "show_stdout_on_release": ,
#     "show_hidden_tests_on_release": ,
#     "seed": ,
#     "grade_from_log": ,
#     "serialized_variables": ,
#     "public_multiplier": ,
#     "token": None,
#     "course_id": '',
#     "assignment_id": '',
#     "filtering": ,
#     "pagebreaks": ,
#     "debug": False,
#     "autograder_dir": '/autograder',
#     "lang": '',
# }

if __name__ == "__main__":
    run_autograder('/autograder')