"""Transformations to apply to a submission before execution"""

import copy
import nbformat


IGNORE_CELL_TAG = "otter_ignore"
CELL_METADATA_KEY = "otter"


def script_to_notebook(script):
    """
    Convert a Python script (a string) to a notebook with ``nbformat``.

    Args:
        script (``str``): the script

    Returns:
        ``nbformat.NotebookNode``: a notebook with a single code cell containing the script
    """
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell(script))
    return nb


def filter_ignored_cells(nb):
    """
    Filter out all cells in the notebook ``nb`` that are tagged with ``otter_ignore`` or have the
    ``ignore`` key of their Otter cell metadata set to true.

    Args:
        nb (``nbformat.NotebookNode``): the notebook

    Returns:
        ``nbformat.NotebookNode``: the notebook with ignored cells removed
    """
    nb = copy.deepcopy(nb)

    to_delete = []
    for i, cell in enumerate(nb["cells"]):
        metadata = cell.get("metadata", {})
        tags = metadata.get("tags", [])

        if IGNORE_CELL_TAG in tags or metadata.get(CELL_METADATA_KEY, {}).get("ignore", False):
            to_delete.append(i)

    to_delete.reverse()
    for i in to_delete:
        del nb["cells"][i]

    return nb


def create_collected_check_cell(cell, notebook_class_name, test_dir):
    """
    Generate a string of calls to ``otter.Notebook.check``.

    Note that this string is formatted with surrounding newlines, so it can be inserted into any
    Python script as-is.

    Args:
        cell (``nbformat.NotebookNode``): the code cell to which checks should be appended
        notebook_class_name(``str``): the name of the ``otter.Notebook`` class in the environment
        test_dir (``str``): the path to the directory of tests.       

    Returns:
        ``str``: the code to run the checks; if no checks are indicated, the empty string
    """
    source = ""
    otter_config = cell.get("metadata", {}).get(CELL_METADATA_KEY, {})

    if otter_config.get("tests", []):
        tests = otter_config.get("tests", [])
        for test in tests:
            source += f"\n{notebook_class_name}(tests_dir='{test_dir}').check('{test}')\n"

    return source
