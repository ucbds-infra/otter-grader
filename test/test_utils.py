"""Tests for ``otter.utils``"""

import pandas as pd

from unittest import mock

from otter.utils import get_variable_type, hide_outputs


@mock.patch("otter.utils.get_ipython")
def test_hide_outputs(mocked_get_ipython):
    """
    Tests for ``otter.utils.hide_outputs``.
    """
    old_formatters = mocked_get_ipython.return_value.display_formatter.formatters
    with hide_outputs():
        assert mocked_get_ipython.return_value.display_formatter.formatters == {}
    assert mocked_get_ipython.return_value.display_formatter.formatters == old_formatters


# Used in test_get_variable_type
class Foo: pass


def test_get_variable_type():
    """
    Tests for ``otter.utils.get_variable_type``.
    """
    assert get_variable_type(Foo()) == "test.test_utils.Foo"
    assert get_variable_type(pd.DataFrame()) == "pandas.core.frame.DataFrame"
