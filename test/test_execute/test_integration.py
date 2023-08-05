import json
import nbformat as nbf
import os
import pytest
import shutil
import tempfile

from otter.check.logs import EventType, Log, LogEntry
from otter.execute import grade_notebook

from ..utils import TestFileManager, write_ok_test


FILE_MANAGER = TestFileManager(__file__)


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


def test_log_execution(temp_dir):
    """
    Test for ``otter.execute.grade_notebook`` when a log is provided.
    """
    log = Log([
        LogEntry(EventType.INIT),
        LogEntry(EventType.CHECK, question="q1"),
        LogEntry(EventType.CHECK, question="q2"),
        LogEntry(EventType.CHECK, question="q3"),
        LogEntry(EventType.BEGIN_EXPORT),
        LogEntry(EventType.END_EXPORT),
    ])

    log.entries[1].shelve({"a": 1, "b": 2})
    log.entries[2].shelve({"a": 1, "b": 2, "c": None})
    log.entries[3].shelve({"a": 2, "b": 2, "c": 3, "d": 4})

    nb = nbf.v4.new_notebook(cells=[
        nbf.v4.new_code_cell("import pandas as pd"),
        nbf.v4.new_code_cell("from pandas import read_csv"),
        nbf.v4.new_code_cell("raise Exception\na, b = 1, 2"),
        nbf.v4.new_code_cell("raise Exception\nc = None"),
        nbf.v4.new_code_cell("raise Exception\na, c, d = 2, 3, 4"),
    ])

    subm_path = os.path.join(temp_dir, "submission.ipynb")
    nbf.write(nb, subm_path)

    test_dir = os.path.join(temp_dir, "tests")
    os.makedirs(test_dir)

    write_ok_test(os.path.join(test_dir, "q1.py"), ">>> assert a == 1 and b == 2")
    write_ok_test(os.path.join(test_dir, "q2.py"), ">>> assert c is None")
    write_ok_test(os.path.join(test_dir, "q3.py"), ">>> assert a == 2 and c == 3 and d == 4")

    results = grade_notebook(subm_path, test_dir=test_dir, log=log, ignore_errors=False)

    with FILE_MANAGER.open("expected_log_results.json") as f:
        expected_results = json.load(f)

    # fix paths to account for the temp directory
    for d in expected_results.values():
        d["path"] = os.path.join(test_dir, os.path.split(d["path"])[1])

    assert results.to_dict() == expected_results
