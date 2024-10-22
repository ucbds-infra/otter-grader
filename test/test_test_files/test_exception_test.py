"""Tests for ``otter.test_files.exception_test``"""

import pprint
import pytest

from textwrap import dedent

from otter.test_files.exception_test import ExceptionTestFile


@pytest.fixture
def exception_test_contents():
    return dedent(
        """\
        from otter.test_files import test_case

        OK_FORMAT = False

        name = "q1"

        @test_case(hidden=False, points=1)
        def q1_1(x):
            assert x % 2 == 0

        @test_case(hidden=True, points=2)
        def q1_2(x):
            assert x == 4
        """
    )


def test_all_or_nothing(exception_test_contents, tmp_path):
    """
    Tests the ``all_or_nothing`` config of an OK test.
    """
    exception_test_contents += "\nall_or_nothing = True"

    test_file = tmp_path / "q1.py"
    test_file.write_text(exception_test_contents)

    # test passes
    tf = ExceptionTestFile.from_file(str(test_file))
    assert tf.all_or_nothing

    tf.run({"x": 4})
    assert tf.grade == 1
    assert tf.score == 3
    assert tf.possible == 3

    # test fails
    tf = ExceptionTestFile.from_file(str(test_file))
    assert tf.all_or_nothing

    tf.run({"x": 5})
    assert tf.grade == 0
    assert tf.score == 0
    assert tf.possible == 3

    # public passes, hidden fails
    tf = ExceptionTestFile.from_file(str(test_file))
    assert tf.all_or_nothing

    tf.run({"x": 2})
    assert tf.grade == 0
    assert tf.score == 0
    assert tf.possible == 3
