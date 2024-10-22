"""Tests for ``otter.test_files.ok_test``"""

import pprint
import pytest

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


def test_all_or_nothing(ok_test_spec, tmp_path):
    """
    Tests the ``all_or_nothing`` config of an OK test.
    """
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
