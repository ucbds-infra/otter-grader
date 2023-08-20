"""Tests for ``otter.api``"""

import os

from unittest import mock

from otter.api import grade_submission


@mock.patch("otter.api.run_grader")
@mock.patch("otter.api.redirect_stdout")
def test_grade_submission(mocked_redirect, mocked_run):
    """
    Tests for ``otter.api.grade_submission``.
    """
    subm_path = "foo.ipynb"

    grade_submission(subm_path)

    mocked_run.assert_called_with(
        subm_path,
        autograder="autograder.zip",
        output_dir=None,
        no_logo=True,
        debug=False,
    )
    mocked_redirect.assert_not_called()

    grade_submission(subm_path, quiet=True)

    mocked_redirect.assert_called()
