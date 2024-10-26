"""Tests for ``otter.test_files.ok_test``"""

import pprint
import pytest

from otter.test_files.abstract_test import TestCase, TestCaseResult
from otter.test_files.ok_test import OKTestFile


@pytest.fixture
def ok_test_spec():
    return {
        "name": "q1",
        "suites": [
            {
                "cases": [
                    {
                        "code": ">>> assert x % 2 == 0",
                        "hidden": False,
                        "points": 1,
                    },
                    {
                        "code": ">>> assert x == 4",
                        "hidden": True,
                        "points": 2,
                    },
                ],
            },
        ],
    }


@pytest.fixture
def ok_test_spec_with_messages():
    return {
        "name": "q1",
        "suites": [
            {
                "cases": [
                    {
                        "code": ">>> assert x % 2 == 0",
                        "hidden": False,
                        "points": 1,
                        "success_message": "foo",
                    },
                    {
                        "code": ">>> assert x == 4",
                        "hidden": True,
                        "points": 2,
                        "failure_message": "bar",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def expected_test_cases():
    return [
        TestCase(
            name="q1 - 1",
            body=">>> assert x % 2 == 0",
            hidden=False,
            points=1,
            success_message=None,
            failure_message=None,
        ),
        TestCase(
            name="q1 - 2",
            body=">>> assert x == 4",
            hidden=True,
            points=2,
            success_message=None,
            failure_message=None,
        ),
    ]


@pytest.fixture
def expected_test_cases_with_messages():
    return [
        TestCase(
            name="q1 - 1",
            body=">>> assert x % 2 == 0",
            hidden=False,
            points=1,
            success_message="foo",
            failure_message=None,
        ),
        TestCase(
            name="q1 - 2",
            body=">>> assert x == 4",
            hidden=True,
            points=2,
            success_message=None,
            failure_message="bar",
        ),
    ]


def test_from_file(
    ok_test_spec,
    ok_test_spec_with_messages,
    expected_test_cases,
    expected_test_cases_with_messages,
    tmp_path,
):
    """Tests ``OKTestFile.from_file``."""
    fp = tmp_path / "foo.py"
    fp.write_text(f"test = {pprint.pformat(ok_test_spec)}")

    tf = OKTestFile.from_file(str(fp))
    assert tf.name == "q1"
    assert tf.path == str(fp)
    assert tf.all_or_nothing == False
    assert tf.test_cases == expected_test_cases

    fp.write_text(f"test = {pprint.pformat(ok_test_spec_with_messages)}")

    tf = OKTestFile.from_file(str(fp))
    assert tf.name == "q1"
    assert tf.path == str(fp)
    assert tf.all_or_nothing == False
    assert tf.test_cases == expected_test_cases_with_messages


@pytest.mark.parametrize(
    "spec, ctx",
    [
        (
            {
                "name": "q1",
                "suites": [
                    {},
                    {},
                ],
            },
            pytest.raises(AssertionError),
        ),
        (
            {
                "suites": [
                    {},
                ],
            },
            pytest.raises(AssertionError),
        ),
        (
            {
                "name": "q1",
                "suites": [
                    {
                        "cases": [
                            {
                                "code": ">>> assert x % 2 == 0",
                                "hidden": False,
                                "points": 1,
                            },
                        ],
                        "type": "a type",
                    },
                ],
            },
            pytest.raises(AssertionError),
        ),
        (
            {
                "name": "q1",
                "suites": [
                    {
                        "cases": [
                            {
                                "code": ">>> assert x % 2 == 0",
                                "hidden": False,
                                "points": 1,
                            },
                        ],
                        "setup": "some code",
                    },
                ],
            },
            pytest.raises(AssertionError),
        ),
        (
            {
                "name": "q1",
                "suites": [
                    {
                        "cases": [
                            {
                                "code": ">>> assert x % 2 == 0",
                                "hidden": False,
                                "points": 1,
                            },
                        ],
                        "teardown": "some code",
                    },
                ],
            },
            pytest.raises(AssertionError),
        ),
    ],
)
def test_from_spec_errors(spec, ctx, tmp_path):
    """Tests errors in ``OKTestFile.from_file``."""
    with ctx:
        OKTestFile.from_spec(spec)


def test_from_metadata(
    ok_test_spec,
    ok_test_spec_with_messages,
    expected_test_cases,
    expected_test_cases_with_messages,
):
    """Tests ``OKTestFile.from_metadata``."""
    tf = OKTestFile.from_metadata(ok_test_spec, "foo.ipynb")
    assert tf.name == "q1"
    assert tf.path == "foo.ipynb"
    assert tf.all_or_nothing == False
    assert tf.test_cases == expected_test_cases

    tf = OKTestFile.from_metadata(ok_test_spec_with_messages, "foo.ipynb")
    assert tf.name == "q1"
    assert tf.path == "foo.ipynb"
    assert tf.all_or_nothing == False
    assert tf.test_cases == expected_test_cases_with_messages


def test_run(ok_test_spec, expected_test_cases, tmp_path):
    """Tests ``OKTestFile.run``."""
    fp = tmp_path / "foo.py"
    fp.write_text(f"test = {pprint.pformat(ok_test_spec)}")

    tf = OKTestFile.from_file(str(fp))

    tf.run({"x": 4})
    assert tf.test_case_results == [
        TestCaseResult(expected_test_cases[0], "✅ Test case passed", True),
        TestCaseResult(expected_test_cases[1], "✅ Test case passed", True),
    ]

    tf.run({"x": 6})
    assert len(tf.test_case_results) == 2
    assert tf.test_case_results[0] == TestCaseResult(
        expected_test_cases[0], "✅ Test case passed", True
    )
    assert tf.test_case_results[1].test_case == expected_test_cases[1]
    assert tf.test_case_results[1].passed == False
    assert tf.test_case_results[1].message.startswith("❌ Test case failed\n")
    assert "assert x == 4" in tf.test_case_results[1].message
    assert "AssertionError" in tf.test_case_results[1].message


def test_all_or_nothing(ok_test_spec, tmp_path):
    """Tests the ``all_or_nothing`` config."""
    ok_test_spec["all_or_nothing"] = True

    test_file = tmp_path / f"{ok_test_spec['name']}.py"
    test_file.write_text("OK_FORMAT = True\ntest = " + pprint.pformat(ok_test_spec))

    # test passes
    tf = OKTestFile.from_file(str(test_file))
    assert tf.all_or_nothing

    tf.run({"x": 4})
    assert tf.grade == 1
    assert tf.score == 3
    assert tf.possible == 3

    # test fails
    tf = OKTestFile.from_file(str(test_file))
    assert tf.all_or_nothing

    tf.run({"x": 5})
    assert tf.grade == 0
    assert tf.score == 0
    assert tf.possible == 3

    # public passes, hidden fails
    tf = OKTestFile.from_file(str(test_file))
    assert tf.all_or_nothing

    tf.run({"x": 2})
    assert tf.grade == 0
    assert tf.score == 0
    assert tf.possible == 3
