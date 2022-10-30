"""Tests for ``otter.execute.execute_log``"""

from types import ModuleType
import nbformat as nbf

from textwrap import dedent
from unittest import mock

from otter.check.logs import EventType, Log, LogEntry
from otter.execute.execute_log import execute_log
from otter.test_files.abstract_test import TestFile


# prevent pytest from trying to collect the TestFile class
TestFile.__test__ = False


def generate_nb():
    nb = nbf.v4.new_notebook()
    nb.cells.append(nbf.v4.new_code_cell(dedent("""\
        import numpy as np
        import pandas as pd
        from glob import glob
    """)))
    nb.cells.append(nbf.v4.new_code_cell(dedent("""\
        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })
        arr = np.random.normal(size=100)
    """)))
    return nb


def generate_question_envs():
    return {
        "q1": {
            "a": 1,
            "b": 2,
        },
        "q2": {
            "a": 1,
            "b": 2,
            "c": None,
        },
        "q3": {
            "a": 2,
            "b": 2,
            "c": 3,
            "d": 4,
        },
    }


@mock.patch("builtins.exec")
def test_execute_log(mocked_exec):
    """
    Tests ``otter.execute.execute_log.execute_log``.
    """
    nb = generate_nb()
    envs = generate_question_envs()
    mocked_log = mock.MagicMock()
    mocked_grader = mock.MagicMock()

    entries = []
    expected_env = {}
    for q in sorted(envs.keys()):
        mocked_entry = mock.MagicMock()
        mocked_entry.unshelve.return_value = envs[q]
        mocked_entry.question = q
        entries.append(mocked_entry)
        expected_env.update(envs[q])

    mocked_log.question_iterator.return_value = entries

    list_name = "check_results_foo123"
    initial_env = {list_name: [], "grader": mocked_grader}

    executed_env = execute_log(nb, mocked_log, check_results_list_name=list_name, initial_env=initial_env)

    mocked_exec.assert_any_call("import otter\ngrader = otter.Notebook()\n", executed_env)
    mocked_exec.assert_any_call("import numpy as np", executed_env)
    mocked_exec.assert_any_call("import pandas as pd", executed_env)
    mocked_exec.assert_any_call("from glob import glob", executed_env)

    for k, v in expected_env.items():
        assert executed_env[k] == v

    assert mocked_grader.check.call_count == len(envs)
    for q in envs.keys():
        mocked_grader.check.assert_any_call(q, global_env=executed_env)
