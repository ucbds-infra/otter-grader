"""
Default configurations for autograding
"""

# a dictionary for documenting each configuration and its default value; the dictionary of actual
# configurations that gets imported is generated from this dictionary
DEFAULT_OPTIONS_WITH_DESCRIPTIONS = {
    "score_threshold": {
        "description": "a score threshold for pass-fail assignments",
        "default": None,
    },
    "points_possible": {
        "description": "a custom total score for the assignment; if unspecified the sum of " \
            "question point values is used.",
        "default": None,
    },
    "show_stdout": {
        "description": "whether to display the autograding process stdout to students on Gradescope",
        "default": False,
    },
    "show_hidden": {
        "description": "whether to display the results of hidden tests to students on Gradescope",
        "default": False,
    },
    "show_all_public": {
        "description": "whether to display all test results if all tests are public tests",
        "default": False,
    },
    "seed": {
        "description": "a random seed for intercell seeding",
        "default": None,
    },
    "grade_from_log": {
        "description": "whether to re-assemble the student's environment from the log rather than " \
            "by re-executing their submission",
        "default": False,
    },
    "serialized_variables": {
        "description": "a mapping of variable names to type strings for validating a deserialized " \
            "student environment",
        "default": {},
    },
    "pdf": {
        "description": "whether to generate a PDF of the notebook when not using Gradescope auto-upload",
        "default": False,
    },
    "token": {
        "description": "a Gradescope token for uploading a PDF of the notebook",
        "default": None,
    },
    "course_id": {
        "description": "a Gradescope course ID for uploading a PDF of the notebook",
        "default": 'None',
    },
    "assignment_id": {
        "description": "a Gradescope assignment ID for uploading a PDF of the notebook",
        "default": 'None',
    },
    "filtering": {
        "description": "whether the generated PDF should have cells filtered out",
        "default": True,
    },
    "pagebreaks": {
        "description": "whether the generated PDF should have pagebreaks between filtered sectios",
        "default": True,
    },
    "debug": {
        "description": "whether to run the autograder in debug mode (without ignoring errors)",
        "default": False,
    },
    "autograder_dir": {
        "description": "the directory in which autograding is taking place",
        "default": '/autograder',
    },
    "lang": {
        "description": "the language of the assignment; one of {'python', 'r'}",
        "default": 'python',
    },
    "miniconda_path": {
        "description": "the path to the miniconda install directory",
        "default": '/root/miniconda3',
    },
    "plugins": {
        "description": "a list of plugin names and configuration details for grading",
        "default": [],
    },
    "logo": {
        "description": "whether to print the Otter logo to stdout",
        "default": True,
    },
    "print_summary": {
        "description": "whether to print the grading summary",
        "default": True,
    },
    "print_score": {
        "description": "whether to print out the submission score in the grading summary",
        "default": True,
    },
    "zips": {
        "description": "whether zip files are being graded",
        "default": False,
    },
}

DEFAULT_OPTIONS = {k: v["default"] for k, v in DEFAULT_OPTIONS_WITH_DESCRIPTIONS.items()}
