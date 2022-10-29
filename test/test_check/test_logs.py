"""Tests for ``otter.check.logs``"""

import os
import pytest
import sys

from sklearn.linear_model import LinearRegression

from otter.check.logs import Log
from otter.check.notebook import Notebook, _OTTER_LOG_FILENAME
from otter.check.logs import LogEntry, EventType, Log

from ..utils import TestFileManager


FILE_MANAGER = TestFileManager(__file__)


@pytest.fixture(autouse=True)
def cleanup_output(cleanup_enabled):
    yield
    if cleanup_enabled and os.path.isfile(_OTTER_LOG_FILENAME):
        os.remove(_OTTER_LOG_FILENAME)


def test_notebook_check():
    test_directory = FILE_MANAGER.get_path("logs-tests")
    grading_results = {}
    grader = Notebook(tests_dir=test_directory)

    def square(x):
        return x**2

    for test_file in os.listdir(test_directory):
        if os.path.splitext(test_file)[1] != ".py":
            continue

        test_name = os.path.splitext(test_file)[0]
        grading_results[test_name] = grader.check(test_name)

    log = Log.from_file(_OTTER_LOG_FILENAME)

    for question in log.get_questions():
        actual_result = grading_results[question]

        # checking repr since the results __eq__ method is not defined
        assert repr(log.get_results(question)) == repr(actual_result), \
            f"Logged results for {question} are not correct"

        logged_grade = log.get_question_entry(question).get_score_perc()
        assert logged_grade == actual_result.grade, f"Logged results for {question} are not correct"

        # checking repr since the results __eq__ method is not defined
        assert repr(log.get_question_entry(question).get_results()) == repr(actual_result), \
            f"Logged results for {question} are not correct"


def test_shelve():
    """
    tests shelve() and unshelve() which call shelve_environment()
    """

    def square(x):
        return x**2

    import calendar 

    env = {
        "num": 5,
        "func": square,
        "model": LinearRegression(),
        "module": sys,
        "ignored_func": calendar.setfirstweekday
    }

    entry = LogEntry(
        event_type=EventType.CHECK,
        results=[],
        question="foo",
        success=True,
        error=None,
    )


    entry.shelve(env, delete=True, filename=_OTTER_LOG_FILENAME, ignore_modules=['calendar'])
    assert entry.shelf
    assert entry.unshelved == ["module", "ignored_func"]

    entry.flush_to_file(_OTTER_LOG_FILENAME) 

    from math import factorial

    log = Log.from_file(_OTTER_LOG_FILENAME)
    entry = log.get_question_entry("foo")
    env = entry.unshelve()
    assert [*env] == ["num", "func", "model"]

    env_with_factorial = entry.unshelve(dict(factorial = factorial))
    assert "factorial" in env_with_factorial["func"].__globals__
    assert factorial is env_with_factorial["func"].__globals__["factorial"]


def test_log_getitem():
    entry = LogEntry(
        event_type=EventType.AUTH,
        results=[],
        question=None, 
        success=True, 
        error=None,
    )
    entry.flush_to_file(_OTTER_LOG_FILENAME)

    log = Log.from_file(_OTTER_LOG_FILENAME)
    assert log[0].event_type == entry.event_type and log[0].results == entry.results


def test_log_iter():
    entry1 = LogEntry(
        event_type=EventType.CHECK,
        results=[],
        question= "q1", 
        success=True, 
        error=None,
    )

    entry2 = LogEntry(
        event_type=EventType.CHECK,
        results=[],
        question= "q1", 
        success=True, 
        error=None,
    )

    entry3 = LogEntry(
        event_type=EventType.CHECK,
        results=[],
        question= "q2", 
        success=True, 
        error=None,
    )

    entry1.flush_to_file(_OTTER_LOG_FILENAME)
    entry2.flush_to_file(_OTTER_LOG_FILENAME)
    entry3.flush_to_file(_OTTER_LOG_FILENAME)

    log = Log.from_file(_OTTER_LOG_FILENAME)

    log_iter = log.question_iterator()
    assert log_iter.questions == ["q1", "q2"]
    assert next(log_iter).question == entry2.question
    assert next(log_iter).question == entry3.question
