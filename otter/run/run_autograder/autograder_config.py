"""Configurations for the autograder"""

import fica

from typing import Any, Literal, Optional, Union


class AutograderConfig(fica.Config):
    """
    Configurations for the autograder.
    """

    score_threshold: Optional[Union[int, float]] = fica.Key(
        description="a score threshold for pass-fail assignments",
        default=None,
    )

    points_possible: Optional[Union[int, float]] = fica.Key(
        description="a custom total score for the assignment; if unspecified the sum of question "
        "point values is used.",
        default=None,
    )

    show_stdout: bool = fica.Key(
        description="whether to display the autograding process stdout to students on Gradescope",
        default=False,
    )

    show_hidden: bool = fica.Key(
        description="whether to display the results of hidden tests to students on Gradescope",
        default=False,
    )

    show_all_public: bool = fica.Key(
        description="whether to display all test results if all tests are public tests",
        default=False,
    )

    seed: Optional[int] = fica.Key(
        description="a random seed for intercell seeding",
        default=None,
    )

    seed_variable: Optional[str] = fica.Key(
        description="a variable name to override with the seed",
        default=None,
    )

    grade_from_log: bool = fica.Key(
        description="whether to re-assemble the student's environment from the log rather than "
        "by re-executing their submission",
        default=False,
    )

    serialized_variables: Optional[dict[str, str]] = fica.Key(
        description="a mapping of variable names to type strings for validating a deserialized "
        "student environment",
        default=None,
    )

    pdf: bool = fica.Key(
        description="whether to generate a PDF of the notebook when not using Gradescope "
        "auto-upload",
        default=False,
    )

    token: Optional[str] = fica.Key(
        description="a Gradescope token for uploading a PDF of the notebook",
        default=None,
    )

    course_id: Optional[Union[int, str]] = fica.Key(
        description="a Gradescope course ID for uploading a PDF of the notebook",
        default=None,
    )

    assignment_id: Optional[Union[int, str]] = fica.Key(
        description="a Gradescope assignment ID for uploading a PDF of the notebook",
        default=None,
    )

    filtering: bool = fica.Key(
        description="whether the generated PDF should have cells filtered out",
        default=False,
    )

    pagebreaks: bool = fica.Key(
        description="whether the generated PDF should have pagebreaks between filtered sections",
        default=False,
    )

    debug: bool = fica.Key(
        description="whether to run the autograder in debug mode (without ignoring errors)",
        default=False,
    )

    autograder_dir: str = fica.Key(
        description="the directory in which autograding is taking place",
        default="/autograder",
    )

    lang: Union[Literal["python"], Literal["r"]] = fica.Key(
        description="the language of the assignment; one of {'python', 'r'}",
        default="python",
        validator=fica.validators.choice(["python", "r"]),
    )

    miniconda_path: str = fica.Key(
        description="the path to the mamba install directory",
        default="/root/miniforge3",
    )

    plugins: list[Union[str, dict[str, Any]]] = fica.Key(
        description="a list of plugin names and configuration details for grading",
        default=[],
    )

    logo: bool = fica.Key(
        description="whether to print the Otter logo to stdout",
        default=True,
    )

    print_summary: bool = fica.Key(
        description="whether to print the grading summary",
        default=True,
    )

    print_score: bool = fica.Key(
        description="whether to print out the submission score in the grading summary",
        default=True,
    )

    zips: bool = fica.Key(
        description="whether zip files are being graded",
        default=False,
    )

    log_level: Optional[int] = fica.Key(
        description="a log level for logging messages; any value suitable for "
        "``logging.Logger.setLevel``",
        default=None,
    )

    assignment_name: Optional[str] = fica.Key(
        description="a name for the assignment to ensure that students submit to the correct "
        "autograder",
        default=None,
    )

    warn_missing_pdf: bool = fica.Key(
        description="whether to add a 0-point public test to the Gradescope output to indicate "
        "to students whether a PDF was found/generated for this assignment",
        default=False,
    )

    force_public_test_summary: bool = fica.Key(
        description="whether to show a summary of public test case results when show_hidden is "
        "true",
        default=True,
    )

    submit_blank_pdf_on_export_failure: bool = fica.Key(
        description="whether to submit a blank PDF to the manual-grading Gradescope assignment "
        "if a PDF cannot be generated from the submission",
        default=False,
    )

    use_submission_pdf: bool = fica.Key(
        description="use the PDF in the submission zip file instead of exporting a new one; if "
        "no PDF is present, a new one is generated anyway; assumes there is only 1 PDF file "
        "in the submission",
        default=False,
    )

    pdf_via_html: bool = fica.Key(
        description="use the PDF via HTML exporter to export the submission PDF; ignored for Rmd "
        "submissions",
        default=False,
    )

    otter_run: bool = False
    """whether this autograder run is being run by Otter Run (i.e. without containerization)"""
