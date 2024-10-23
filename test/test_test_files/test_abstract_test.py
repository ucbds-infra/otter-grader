"""Tests for ``otter.test_files.abstract_test``"""

import pytest
import random

from dataclasses import asdict
from unittest import mock

from otter.test_files.abstract_test import TestCase, TestCaseResult, TestFile


class MockTestFile(TestFile):
    """A ``TestFile`` for testing the ABC's methods."""

    _test_cases: list[TestCase]

    @classmethod
    def from_file(cls, path):
        return cls(path, path, cls._test_cases)

    @classmethod
    def from_metadata(cls, s, path):
        return cls(path, path, cls._test_cases)

    def run(self, global_environment):
        tcrs: list[TestCaseResult] = []
        for i, tc in enumerate(self.test_cases):
            passed = global_environment[tc.name]
            tcrs.append(TestCaseResult(tc, None if passed else ":(", passed))
        self.test_case_results = tcrs


@pytest.fixture(autouse=True)
def reset_mock_test_file():
    MockTestFile._test_cases = [
        TestCase("q1", "q1 body", False, 1, None, None),
        TestCase("q1H", "q1 body", True, 1, None, None),
        TestCase("q2", "q2 body", False, 1, "q2 success", None),
        TestCase("q2H", "q2 body", True, 2, "q2H success", None),
        TestCase("q3", "q3 body", False, 0, None, "q3 failure"),
        TestCase("q3H", "q3 body", True, 1, None, "q3H failure"),
    ]


def make_test_case(**kwargs):
    return TestCase(
        **{
            "name": "q1",
            "body": "q1 body",
            "points": 1,
            "hidden": False,
            "success_message": None,
            "failure_message": None,
            **kwargs,
        },
    )


def test_repr():
    """Tests ``TestFile.__repr__``"""
    tf = MockTestFile.from_file("foo")
    with mock.patch.object(tf, "summary", return_value="foobar") as mocked_summary:
        repr(tf)
        mocked_summary.assert_called_once_with()


@pytest.mark.parametrize(
    "test_cases_override, test_case_results, want",
    [
        (
            [
                TestCase("q1", "q1 body", False, 1, None, None),
                TestCase("q1H", "q1 body", True, 1, None, None),
            ],
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            "<p><strong><pre style='display: inline;'>foo</pre></strong> passed! 🎉</p>",
        ),
        (
            None,
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            (
                "<p><strong><pre style='display: inline;'>foo</pre></strong> passed! 🎉</p>"
                "<p><strong><pre style='display: inline;'>q2</pre> message:</strong> q2 success</p>"
                "<p><strong><pre style='display: inline;'>q2H</pre> message:</strong> q2H success</p>"
            ),
        ),
        (
            None,
            {
                "q1": False,
                "q1H": True,
                "q2": True,
                "q2H": False,
                "q3": False,
                "q3H": False,
            },
            (
                "<p><strong style='color: red;'><pre style='display: inline;'>foo</pre> results:</strong></p>"
                "<p><strong><pre style='display: inline;'>q1</pre> result:</strong></p>"
                "<pre>    :(</pre>"
                "<p><strong><pre style='display: inline;'>q1H</pre> result:</strong></p>"
                "<pre></pre>"
                "<p><strong><pre style='display: inline;'>q2</pre> message:</strong> q2 success</p>"
                "<p><strong><pre style='display: inline;'>q2</pre> result:</strong></p>"
                "<pre></pre>"
                "<p><strong><pre style='display: inline;'>q2H</pre> result:</strong></p>"
                "<pre>    :(</pre>"
                "<p><strong><pre style='display: inline;'>q3</pre> message:</strong> q3 failure</p>"
                "<p><strong><pre style='display: inline;'>q3</pre> result:</strong></p>"
                "<pre>    :(</pre>"
                "<p><strong><pre style='display: inline;'>q3H</pre> message:</strong> q3H failure</p>"
                "<p><strong><pre style='display: inline;'>q3H</pre> result:</strong></p>"
                "<pre>    :(</pre>"
            ),
        ),
    ],
)
def test_repr_html(test_cases_override, test_case_results, want):
    """Tests ``TestFile._repr_html_``"""
    if test_cases_override is not None:
        MockTestFile._test_cases = test_cases_override
    random.seed(42)
    tf = MockTestFile.from_file("foo")
    tf.run(test_case_results)
    assert tf._repr_html_() == want


@pytest.mark.parametrize(
    "total_points, test_cases, want",
    [
        (
            None,
            [
                make_test_case(points=None),
                make_test_case(points=None),
                make_test_case(points=None),
            ],
            [
                make_test_case(points=1 / 3),
                make_test_case(points=1 / 3),
                make_test_case(points=1 / 3),
            ],
        ),
        (
            None,
            [
                make_test_case(points=1),
                make_test_case(points=1),
                make_test_case(points=1),
            ],
            [
                make_test_case(points=1),
                make_test_case(points=1),
                make_test_case(points=1),
            ],
        ),
        (
            2,
            [
                make_test_case(points=None),
                make_test_case(points=None),
                make_test_case(points=None),
            ],
            [
                make_test_case(points=2 / 3),
                make_test_case(points=2 / 3),
                make_test_case(points=2 / 3),
            ],
        ),
        (
            2,
            [
                make_test_case(points=1),
                make_test_case(points=0.5),
                make_test_case(points=0.5),
            ],
            [
                make_test_case(points=1),
                make_test_case(points=0.5),
                make_test_case(points=0.5),
            ],
        ),
        (
            4,
            [
                make_test_case(points=1),
                make_test_case(points=None),
                make_test_case(points=None),
            ],
            [
                make_test_case(points=1),
                make_test_case(points=1.5),
                make_test_case(points=1.5),
            ],
        ),
        (
            4,
            [
                make_test_case(points=1),
                make_test_case(points=3),
                make_test_case(points=None),
            ],
            [
                make_test_case(points=1),
                make_test_case(points=3),
                make_test_case(points=0),
            ],
        ),
        (
            None,
            [
                make_test_case(points=0),
                make_test_case(points=0),
                make_test_case(points=0),
            ],
            [
                make_test_case(points=0),
                make_test_case(points=0),
                make_test_case(points=0),
            ],
        ),
        (
            None,
            [
                make_test_case(points=0),
                make_test_case(points=None),
                make_test_case(points=None),
            ],
            [
                make_test_case(points=0),
                make_test_case(points=0.5),
                make_test_case(points=0.5),
            ],
        ),
        (
            [1, 2, 3],
            [
                make_test_case(points=None),
                make_test_case(points=None),
                make_test_case(points=None),
            ],
            [
                make_test_case(points=1),
                make_test_case(points=2),
                make_test_case(points=3),
            ],
        ),
        (
            [1, 2, 3],
            [
                make_test_case(points=0.5),
                make_test_case(points=0.5),
                make_test_case(points=0.5),
            ],
            [
                make_test_case(points=1),
                make_test_case(points=2),
                make_test_case(points=3),
            ],
        ),
    ],
)
def test_resolve_test_file_points(total_points, test_cases, want):
    """Tests ``TestFile.resolve_test_file_points``"""
    assert TestFile.resolve_test_file_points(total_points, test_cases) == want


def test_resolve_test_file_points_errors():
    """Tests errors in ``TestFile.resolve_test_file_points``"""
    with pytest.raises(
        ValueError, match="Points specified in test has different length than number of test cases"
    ):
        TestFile.resolve_test_file_points([1, 2], [make_test_case()])

    with pytest.raises(TypeError, match="Test spec points has invalid type: <class 'str'>"):
        TestFile.resolve_test_file_points("foo", [])

    with pytest.raises(
        ValueError, match="More points specified in test cases than allowed for test"
    ):
        TestFile.resolve_test_file_points(
            1, [make_test_case(points=2), make_test_case(points=None)]
        )


@pytest.mark.parametrize(
    "test_case_results, want",
    [
        (
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            True,
        ),
        (
            {
                "q1": True,
                "q1H": False,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            False,
        ),
        (
            {
                "q1": True,
                "q1H": True,
                "q2": False,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            False,
        ),
    ],
)
def test_passed_all(test_case_results, want):
    """Tests ``TestFile.passed_all``"""
    tf = MockTestFile.from_file("foo")
    tf.run(test_case_results)
    assert tf.passed_all == want


@pytest.mark.parametrize(
    "test_case_results, want",
    [
        (
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            True,
        ),
        (
            {
                "q1": True,
                "q1H": False,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            True,
        ),
        (
            {
                "q1": True,
                "q1H": True,
                "q2": False,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            False,
        ),
    ],
)
def test_passed_all_public(test_case_results, want):
    """Tests ``TestFile.passed_all_public``"""
    tf = MockTestFile.from_file("foo")
    tf.run(test_case_results)
    assert tf.passed_all_public == want


@pytest.mark.parametrize(
    "test_cases, want",
    [
        (
            [
                make_test_case(hidden=True),
                make_test_case(hidden=False),
            ],
            False,
        ),
        (
            [
                make_test_case(hidden=False),
                make_test_case(hidden=False),
            ],
            True,
        ),
    ],
)
def test_all_public(test_cases, want):
    """Tests ``TestFile.all_public``"""
    MockTestFile._test_cases = test_cases
    tf = MockTestFile.from_file("foo")
    assert tf.all_public == want


@pytest.mark.parametrize(
    "test_case_results, all_or_nothing, want_grade, want_score, want_possible",
    [
        (
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            False,
            1,
            6,
            6,
        ),
        (
            {
                "q1": True,
                "q1H": False,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            False,
            5 / 6,
            5,
            6,
        ),
        (
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            True,
            1,
            6,
            6,
        ),
        (
            {
                "q1": True,
                "q1H": False,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            True,
            0,
            0,
            6,
        ),
        (
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": False,
                "q3H": True,
            },
            False,
            1,
            6,
            6,
        ),
        (
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                # NOTE: q3 is worth 0 points, but all_or_nothing overrides this, causing the test
                # file to get a score of 0
                "q3": False,
                "q3H": True,
            },
            True,
            0,
            0,
            6,
        ),
    ],
)
def test_grade_score_possible(
    test_case_results, all_or_nothing, want_grade, want_score, want_possible
):
    """Tests ``TestFile.grade``, ``TestFile.score``, and ``TestFile.possible``"""
    tf = MockTestFile.from_file("foo")
    tf.all_or_nothing = all_or_nothing
    tf.run(test_case_results)
    assert tf.grade == want_grade
    assert tf.score == want_score
    assert tf.possible == want_possible


def test_update_score():
    """Tests ``TestFile.update_score``"""
    tf = MockTestFile.from_file("foo")
    tf.run(
        {
            "q1": True,
            "q1H": True,
            "q2": True,
            "q2H": True,
            "q3": True,
            "q3H": True,
        }
    )
    assert tf.score == 6
    tf.update_score(1)
    assert tf.score == 1


def test_to_dict():
    """Tests ``TestFile.to_dict``"""
    tf = MockTestFile.from_file("foo")
    tf.run(
        {
            "q1": True,
            "q1H": False,
            "q2": True,
            "q2H": True,
            "q3": True,
            "q3H": True,
        }
    )
    assert tf.to_dict() == {
        "score": 0,
        "possible": 6,
        "name": "foo",
        "path": "foo",
        "test_cases": [asdict(tc) for tc in MockTestFile._test_cases],
        "all_or_nothing": True,
        "test_case_results": [
            {
                "test_case": asdict(tc),
                "message": None if tc.name != "q1H" else ":(",
                "passed": tc.name != "q1H",
            }
            for tc in MockTestFile._test_cases
        ],
    }


@pytest.mark.parametrize(
    "test_cases_override, test_case_results, public_only, want",
    [
        (
            [
                TestCase("q1", "q1 body", False, 1, None, None),
                TestCase("q1H", "q1 body", True, 1, None, None),
            ],
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            False,
            "foo results: All test cases passed!",
        ),
        (
            None,
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            False,
            (
                "foo results: All test cases passed!\n"
                "q2 message: q2 success\n"
                "q2H message: q2H success"
            ),
        ),
        (
            None,
            {
                "q1": False,
                "q1H": True,
                "q2": True,
                "q2H": False,
                "q3": False,
                "q3H": False,
            },
            False,
            (
                "foo results:\n"
                "    q1 result:\n"
                "        :(\n"
                "\n"
                "    q1H result:\n"
                "\n"
                "    q2 message: q2 success\n"
                "\n"
                "    q2 result:\n"
                "\n"
                "    q2H result:\n"
                "        :(\n"
                "\n"
                "    q3 message: q3 failure\n"
                "\n"
                "    q3 result:\n"
                "        :(\n"
                "\n"
                "    q3H message: q3H failure\n"
                "\n"
                "    q3H result:\n"
                "        :("
            ),
        ),
        (
            [
                TestCase("q1", "q1 body", False, 1, None, None),
                TestCase("q1H", "q1 body", True, 1, None, None),
            ],
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            True,
            "foo results: All test cases passed!",
        ),
        (
            None,
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": True,
                "q3": True,
                "q3H": True,
            },
            True,
            ("foo results: All test cases passed!\nq2 message: q2 success"),
        ),
        (
            None,
            {
                "q1": True,
                "q1H": True,
                "q2": True,
                "q2H": False,
                "q3": True,
                "q3H": True,
            },
            True,
            ("foo results: All test cases passed!\nq2 message: q2 success"),
        ),
        (
            None,
            {
                "q1": False,
                "q1H": True,
                "q2": True,
                "q2H": False,
                "q3": False,
                "q3H": False,
            },
            True,
            (
                "foo results:\n"
                "    q1 result:\n"
                "        :(\n"
                "\n"
                "    q2 message: q2 success\n"
                "\n"
                "    q2 result:\n"
                "\n"
                "    q3 message: q3 failure\n"
                "\n"
                "    q3 result:\n"
                "        :("
            ),
        ),
    ],
)
def test_summary(test_cases_override, test_case_results, public_only, want):
    """Tests ``TestFile.summary``"""
    if test_cases_override is not None:
        MockTestFile._test_cases = test_cases_override
    random.seed(42)
    tf = MockTestFile.from_file("foo")
    tf.run(test_case_results)
    assert tf.summary(public_only=public_only) == want
