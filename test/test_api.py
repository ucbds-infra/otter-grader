"""Tests for ``otter.api``"""

import os

from unittest import mock

from otter.api import grade_submission


@mock.patch("otter.api.run_grader")
@mock.patch("otter.api.tempfile")
@mock.patch("otter.api.redirect_stdout")
def test_grade_submission(mocked_redirect, mocked_tempfile, mocked_run, tmp_path):
    """
    Tests for ``otter.api.grade_submission``.
    """
    subm_path = "foo.ipynb"
    temp_dir = str(tmp_path / "autograder")
    os.mkdir(temp_dir)

    mocked_tempfile.mkdtemp.return_value = temp_dir

    grade_submission(subm_path)

    mocked_run.assert_called_with(
        subm_path,
        autograder="autograder.zip",
        output_dir=temp_dir,
        no_logo=True,
        debug=False,
    )
    mocked_redirect.assert_not_called()

    os.mkdir(temp_dir)
    grade_submission(subm_path, quiet=True)

    mocked_redirect.assert_called()
