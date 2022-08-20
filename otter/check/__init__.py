"""Otter Check command-line utility"""

import os

from glob import glob

from .logs import LogEntry, EventType
from .notebook import _OTTER_LOG_FILENAME

from ..execute import grade_notebook
from ..utils import block_print, loggers


_ALLOWED_EXTENSIONS = {".py", ".ipynb"}
LOGGER = loggers.get_logger(__name__)


def _log_event(event_type, results=[], question=None, success=True, error=None):
    """
    Logs an event

    Args:
        event_type (``otter.logs.EventType``): the type of event
        results (``list`` of ``otter.test_files.abstract_test.TestCollectionResults``, optional): the 
            results of any checks recorded by the entry
        question (``str``, optional): the question name for this check
        success (``bool``, optional): whether the operation was successful
        error (``Exception``, optional): the exception thrown by the operation, if applicable
    """
    LOGGER.debug(f"Creating a LogEntry of type {event_type}")

    LogEntry(
        event_type,
        results=results,
        question=question, 
        success=success, 
        error=error
    ).flush_to_file(_OTTER_LOG_FILENAME)

    LOGGER.debug(f"LogEntry created successfully")


def main(file, *, tests_path="./tests", question=None, seed=None):
    """
    Runs Otter Check

    Args:
        file (``str``): path to the file to check
        tests_path (``str``): path to tests directory
        question (``str``): test name to run; ``None`` if all tests should be run
        seed (``int``): a seed to set before execution
        **kwargs: ignored kwargs (a remnant of how the argument parser is built)
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

            qs = glob(os.path.join(tests_path, "*.py"))

            LOGGER.debug(f"Found test files: {', '.join(qs)}")

        LOGGER.debug(f"Checking for existence of submission file '{file}'")
        if not os.path.isfile(file):
            raise FileNotFoundError(f"{file} does not exist")

        ext = os.path.splitext(file)[1]
        LOGGER.debug(f"Found submission file extension: '{ext}'")

        if ext not in _ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid extension for file '{ext}'; must be one of {_ALLOWED_EXTENSIONS}")

        script = ext == ".py"
        LOGGER.debug(f"Determined if submission is a Python script: {script}")

        LOGGER.debug(f"Seed value: {seed}")
        LOGGER.info("Grading submission")
        with block_print():
            results = grade_notebook(
                file,
                tests_glob=qs,
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
