"""Tests for ``otter.check.utils``"""

import time

from unittest import mock

from otter.check.utils import save_notebook


@mock.patch("otter.check.utils.os.path.getsize")
@mock.patch("otter.check.utils.os.path.getmtime")
@mock.patch("otter.check.utils.ipylab")
@mock.patch("otter.check.utils.Javascript")
@mock.patch("otter.check.utils.display")
@mock.patch("otter.check.utils.get_ipython")
def test_save_notebook(
    mocked_get_ipython,
    mocked_display,
    mocked_Javascript,
    mocked_ipylab,
    mocked_getmtime,
    mocked_getsize,
):
    """
    Tests for ``otter.check.utils.save_notebook``.
    """
    # check unsuccessful save
    mocked_getsize.return_value = 1
    mocked_getmtime.return_value = 1.0

    start = time.time()
    assert not save_notebook("foo.ipynb")
    end = time.time()

    assert end - start > 10  # check that it slept in between checks
    mocked_display.assert_called_with(mocked_Javascript.return_value)
    mocked_ipylab.JupyterFrontEnd.return_value.commands.execute.assert_called_with("docmanager:save")

    # check successful save
    mocked_getmtime.side_effect = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0]

    mocked_display.reset_mock()

    start = time.time()
    assert save_notebook("foo.ipynb")
    end = time.time()

    assert end - start > 1  # check that it slept in between checks
    mocked_display.assert_called_with(mocked_Javascript.return_value)
    mocked_ipylab.JupyterFrontEnd.return_value.commands.execute.assert_called_with("docmanager:save")

    mocked_display.reset_mock()

    # check that returns true if not running in IPython
    mocked_get_ipython.return_value = None
    assert save_notebook("foo.ipynb")
    mocked_display.assert_not_called()
