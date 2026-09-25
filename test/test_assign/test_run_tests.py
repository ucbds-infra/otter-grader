"""Tests for ``otter.assign.utils.run_tests``"""

import pytest

from types import SimpleNamespace
from unittest import mock

from otter.assign.utils import run_tests
from otter.test_files import GradingResults


def make_test_file(name, score, possible):
    """
    Creates a minimal stand-in for a test file with the given score.
    """
    return SimpleNamespace(
        name=name,
        score=score,
        possible=possible,
        summary=lambda public_only=False: f"{name}: {score}/{possible}",
    )


def call_run_tests(results):
    """
    Calls ``run_tests`` with grading mocked to return ``results``.
    """
    with mock.patch("otter.assign.utils.grade_submission", return_value=results):
        run_tests(mock.MagicMock())


def test_perfect_score_passes():
    """
    A notebook that earns every point passes.
    """
    call_run_tests(GradingResults([make_test_file("q1", 1, 1), make_test_file("q2", 2, 2)]))


def test_partial_score_raises():
    """
    A notebook that does not earn every point raises.
    """
    results = GradingResults([make_test_file("q1", 1, 1), make_test_file("q2", 0, 2)])
    with pytest.raises(RuntimeError, match="Some autograder tests failed"):
        call_run_tests(results)


def test_catastrophic_failure_raises():
    """
    Grading that produced no results (a ``0/0`` score) raises rather than counting as a pass.
    """
    results = GradingResults.without_results(FileNotFoundError("./tests/q1.py"))
    assert results.total == results.possible == 0

    with pytest.raises(RuntimeError, match="did not produce any results") as exc_info:
        call_run_tests(results)

    assert "./tests/q1.py" in str(exc_info.value)
