"""Tests for ``otter.api``"""

import os

from unittest import mock

from otter.api import grade_submission


def test_grade_submission(tmp_path):
    """
    """
    subm_path = "foo.ipynb"
    temp_dir = str(tmp_path / "autograder")
    os.mkdir(temp_dir)

    with mock.patch("otter.api.run_grader") as mocked_run, \
            mock.patch("otter.api.tempfile") as mocked_tempfile, \
            mock.patch("otter.api.redirect_stdout") as mocked_redirect:
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
