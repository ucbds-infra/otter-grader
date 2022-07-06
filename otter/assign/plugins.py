"""Plugin replacement for Otter Assign"""

import copy
import yaml

from .utils import get_source


BEGIN = "# BEGIN PLUGIN"
END = "# END PLUGIN"
BEGIN_EXPORT = "# BEGIN PLUGIN EXPORT"


def replace_plugins(lines):
    """
    Replace plugin blocks with plugin calls in a cell's source (a list of strings).

    Args:
        lines (``list[str]``): the cell source

    Returns:
        ``list[str]``: a copy of ``lines`` with plugin calls
    """
    starts, ends = [], []
    stripped = [[]]
    exports = []
    plugin = False
    for i, line in enumerate(lines):
        if line.rstrip().endswith(END):
            assert plugin, f"END PLUGIN without BEGIN PLUGIN found in {lines}"
            plugin = False
            ends.append(i)
            stripped.append([])

        elif line.rstrip().endswith(BEGIN):
            assert not plugin, f"Nested plugins found in {lines}"
            starts.append(i)
            exports.append(False)
            plugin = True

        elif line.rstrip().endswith(BEGIN_EXPORT):
            assert not plugin, f"Nested plugins found in {lines}"
            starts.append(i)
            exports.append(True)
            plugin = True

        elif plugin:
            stripped[len(starts) - 1].append(line)

    assert len(stripped) == len(starts) + 1 == len(ends) + 1 == len(exports) + 1, f"Error processing plugins in {lines}"
    assert all(s < e for s, e in zip(starts, ends))

    starts.reverse()
    ends.reverse()
    stripped.reverse()
    stripped = stripped[1:]

    lines = lines.copy()

    for i, (s, e) in enumerate(zip(starts, ends)):
        config = yaml.full_load("\n".join(stripped[i]))
        export = exports[i]
        pg = config["plugin"]
        args = ", ".join(config.get("args", []))
        kwargs = ", ".join([f"{k}={v}" for k, v in config.get("kwargs", {}).items()])

        call = ("run_plugin", "add_plugin_files")[export]

        call = f'grader.{call}("{pg}"'
        if args:
            call += f', {args}'
        if kwargs:
            call += f', {kwargs}'
        call += ')'

        del lines[s:e+1]
        lines.insert(s, call)

    return lines


def replace_plugins_with_calls(nb):
    """
    Replace all plugin blocks in a notebook with plugin calls.

    Args:
        nb (``nbformat.NotebookNode``): the notebook

    Returns:
        ``nbformat.NotebookNode``: a copy of ``nb`` with plugin blocks replaced
    """
    nb = copy.deepcopy(nb)

    for cell in nb['cells']:
        cell['source'] = '\n'.join(replace_plugins(get_source(cell)))

    return nb
