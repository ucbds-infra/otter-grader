"""Configurations for the autograder"""

import fica


class AutograderConfig(fica.Config):
    """
    Configurations for the autograder.
    """

    score_threshold = fica.Key(
        description="a score threshold for pass-fail assignments",
        default=None,
    )

    points_possible = fica.Key(
        description="a custom total score for the assignment; if unspecified the sum of question " \
            "point values is used.",
        default=None,
    )

    show_stdout = fica.Key(
        description="whether to display the autograding process stdout to students on Gradescope",
        default=False,
    )

    show_hidden = fica.Key(
        description="whether to display the results of hidden tests to students on Gradescope",
        default=False,
    )

    show_all_public = fica.Key(
        description="whether to display all test results if all tests are public tests",
        default=False,
    )

    seed = fica.Key(
        description="a random seed for intercell seeding",
        default=None,
    )

    seed_variable = fica.Key(
        description="a variable name to override with the seed",
        default=None,
    )

    grade_from_log = fica.Key(
        description="whether to re-assemble the student's environment from the log rather than " \
            "by re-executing their submission",
        default=False,
    )

    serialized_variables = fica.Key(
        description="a mapping of variable names to type strings for validating a deserialized " \
            "student environment",
        default=None,
    )

    pdf = fica.Key(
        description="whether to generate a PDF of the notebook when not using Gradescope " \
            "auto-upload",
        default=False,
    )

    token = fica.Key(
        description="a Gradescope token for uploading a PDF of the notebook",
        default=None,
    )

    course_id = fica.Key(
        description="a Gradescope course ID for uploading a PDF of the notebook",
        default="None",
    )

    assignment_id = fica.Key(
        description="a Gradescope assignment ID for uploading a PDF of the notebook",
        default="None",
    )

    filtering = fica.Key(
        description="whether the generated PDF should have cells filtered out",
        default=False,
    )

    pagebreaks = fica.Key(
        description="whether the generated PDF should have pagebreaks between filtered sections",
        default=False,
    )

    debug = fica.Key(
        description="whether to run the autograder in debug mode (without ignoring errors)",
        default=False,
    )

    autograder_dir = fica.Key(
        description="the directory in which autograding is taking place",
        default="/autograder",
    )

    lang = fica.Key(
        description="the language of the assignment; one of {'python', 'r'}",
        default="python",
        validator=fica.validators.choice(["python", "r"]),
    )

    miniconda_path = fica.Key(
        description="the path to the miniconda install directory",
        default="/root/miniconda3",
    )

    plugins = fica.Key(
        description="a list of plugin names and configuration details for grading",
        default=[],
    )

    logo = fica.Key(
        description="whether to print the Otter logo to stdout",
        default=True,
    )

    print_summary = fica.Key(
        description="whether to print the grading summary",
        default=True,
    )

    print_score = fica.Key(
        description="whether to print out the submission score in the grading summary",
        default=True,
    )

    zips = fica.Key(
        description="whether zip files are being graded",
        default=False,
    )

    log_level = fica.Key(
        description="a log level for logging messages; any value suitable for " \
            "``logging.Logger.setLevel``",
        default=None,
    )

    channel_priority_strict = fica.Key(
        description="whether to set conda's channel_priority config to strict in the setup.sh file",
        default=True,
    )

    assignment_name = fica.Key(
        description="a name for the assignment to ensure that students submit to the correct " \
            "autograder",
        default=None,
    )

    warn_missing_pdf = fica.Key(
        description="whether to add a 0-point public test to the Gradescope output to indicate " \
            "to students whether a PDF was found/generated for this assignment",
        default=False,
    )

    force_public_test_summary = fica.Key(
        description="whether to show a summary of public test case results when show_hidden is " \
            "true",
        default=True,
    )
