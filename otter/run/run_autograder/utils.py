"""Utilities for Otter Run"""

import re
import nbformat

from ...utils import get_source


class OtterRuntimeError(RuntimeError):
    """
    A an error inheriting from ``RuntimeError`` for Otter to throw during a grading process.
    """


def replace_notebook_instances(nb_path):
    """
    Replaces the creation of ``otter.Notebook`` instances in a notebook at ``nb_path`` that have custom 
    test paths with the default for Gradescope.

    Args:
        nb_path (``str``): path to the notebook
    """
    try:
        nb = nbformat.read(nb_path, as_version=nbformat.NO_CONVERT)
        script = False
    except nbformat.reader.NotJSONError:
        nb = nbformat.v4.new_notebook()
        with open(nb_path) as f:
            source = f.read()
        nb['cells'].append(nbformat.v4.new_code_cell(source))
        script = True

    instance_regex = r"otter.Notebook\([\"'].+[\"']\)"
    for cell in nb['cells']:
        source = get_source(cell)
        for i, line in enumerate(source):
            line = re.sub(instance_regex, "otter.Notebook()", line)
            source[i] = line
        cell['source'] = "\n".join(source)

    if not script:
        nbformat.write(nb, nb_path)
    else:
        source = get_source(nb['cells'][0])
        with open(nb_path, "w") as f:
            f.write("\n".join(source))
