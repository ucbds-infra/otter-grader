"""Otter Check command-line utility"""

import os

from typing import Optional

from .logs import EventType, LogEntry
from .notebook import OTTER_LOG_FILENAME
from .utils import list_test_files
from .. import logging
from ..execute import grade_notebook
from ..test_files import GradingResults


ALLOWED_EXTENSIONS = {".py", ".ipynb"}
LOGGER = logging.get_logger(__name__)


def _log_event(
    event_type: EventType,
    results: Optional[list[GradingResults]] = None,
    question: Optional[str] = None,
    success: bool = True,
    error: Optional[Exception] = None,
):
    """
    Logs an event

    Args:
        event_type (``otter.logs.EventType``): the type of event
        results (``list[otter.test_files.GradingResults]``): the
            results of any checks recorded by the entry
        question (``str | None``): the question name for this check
        success (``bool``): whether the operation was successful
        error (``Exception | None``): the exception thrown by the operation, if applicable
    """
    LOGGER.debug(f"Creating a LogEntry of type {event_type}")

    LogEntry(
        event_type, results=results, question=question, success=success, error=error
    ).flush_to_file(OTTER_LOG_FILENAME)

    LOGGER.debug(f"LogEntry created successfully")


def main(
    file: str,
    *,
    tests_path: str = "./tests",
    question: Optional[str] = None,
    seed: Optional[int] = None,
):
    """
    Runs Otter Check

    Args:
        file (``str``): path to the file to check
        tests_path (``str``): path to tests directory
        question (``str | None``): test name to run; ``None`` if all tests should be run
        seed (``int | None``): a seed to set before execution
    """
    try:
        if question:
            LOGGER.debug(f"Determining question '{question}' test path in directory '{tests_path}'")

            test_path = os.path.join(tests_path, question + ".py")
            if not os.path.isfile(test_path):
                raise FileNotFoundError(f"Test {question} does not exist")

            LOGGER.info(f"Found test file {test_path}")
            qs = [test_path]

        else:
            LOGGER.info(f"Searching for test files in tests directory")

            qs = list_test_files(tests_path)

            LOGGER.debug(f"Found test files: {', '.join(qs)}")

        LOGGER.debug(f"Checking for existence of submission file '{file}'")
        if not os.path.isfile(file):
            raise FileNotFoundError(f"{file} does not exist")

        ext = os.path.splitext(file)[1]
        LOGGER.debug(f"Found submission file extension: '{ext}'")

        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid extension for file '{ext}'; must be one of {ALLOWED_EXTENSIONS}"
            )

        script = ext == ".py"
        LOGGER.debug(f"Determined if submission is a Python script: {script}")

        LOGGER.debug(f"Seed value: {seed}")
        LOGGER.info("Grading submission")

        results = grade_notebook(
            file,
            tests_glob=qs,
            test_dir=tests_path,
            script=script,
            seed=seed,
        )

        percentage = results.total / results.possible
        LOGGER.debug(f"Determined score percentage: {percentage}")

        if percentage == 1:
            output = "All tests passed!"

        else:
            output = "\n".join(repr(test_file) for _, test_file in results.results.items())

        print(output)

    except Exception as e:
        _log_event(EventType.CHECK, success=False, error=e)
        raise e

    else:
        _log_event(EventType.CHECK, results=results)
