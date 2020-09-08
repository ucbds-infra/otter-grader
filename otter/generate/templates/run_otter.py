"""
Runs Otter on Gradescope with the configurations specified below
"""

import os
import subprocess

from otter.generate.run_autograder import main as run_autograder

config = {
    "score_threshold": {{ threshold }},
    "points_possible": {{ points }},
    "show_stdout_on_release": {{ show_stdout }},
    "show_hidden_tests_on_release": {{ show_hidden }},
    "seed": {{ seed }},
    "grade_from_log": {{ grade_from_log }},
    "serialized_variables": {{ serialized_variables }},
    "public_multiplier": {{ public_multiplier }},
    "token": {% if token %}'{{ token }}'{% else %}None{% endif %},
    "course_id": '{{ course_id }}',
    "assignment_id": '{{ assignment_id }}',
    "filtering": {{ filtering }},
    "pagebreaks": {{ pagebreaks }},
    "debug": False,
    "autograder_dir": '{{ autograder_dir }}',
    "lang": '{{ lang }}',
}

if __name__ == "__main__":
    run_autograder(config)
