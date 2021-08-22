"""Plugin replacement for Otter Assign"""

import re
import yaml
import nbformat

from .utils import get_source


BEGIN = "# BEGIN PLUGIN"
END = "# END PLUGIN"
BEGIN_EXPORT = "# BEGIN PLUGIN EXPORT"


def replace_plugins(lines):
    """
    Replaces plugins with calls in ``lines``
    
    Args:
        lines (``list`` of ``str``): cell contents as a list of strings

    Returns:
        ``list`` of ``str``: stripped version of lines with plugin calls
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
    Write a notebook with plugins replaced with calls
    
    Args:
        nb (``nbformat.NotebookNode``): the notebook
    """
    for cell in nb['cells']:
        cell['source'] = '\n'.join(replace_plugins(get_source(cell)))
    
    return nb
