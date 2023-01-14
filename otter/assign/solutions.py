"""Solution removal for Otter Assign"""

import copy
import re

from .r_adapter import solutions as r_solutions
from .utils import get_notebook_language, get_source, has_tag, is_cell_type, remove_output, \
    remove_tag


BLOCK_PROMPT = "..."
SOLUTION_CELL_TAG = "otter_assign_solution_cell"


def has_seed(cell):
    """
    Determine whether a cell contains a seed line (a line ending in ``# SEED``).

    Args:
        cell (``nbformat.NotebookNode``): the cell

    Returns:
        ``bool``: whether the cell has a seed line
    """
    if not is_cell_type(cell, "code"):
        return False
    source = get_source(cell)
    return source and any([l.strip().endswith('# SEED') for l in source])


def overwrite_seed_vars(nb, seed_variable, seed):
    """
    Overwrite any assignments of the variable named ``seed_variable`` with the value ``seed`` in a
    notebook.

    Args:
        nb (``nbformat.NotebookNode``): the notebook to edit
        seed_variable (``str``): the variable to look for
        seed (``int``): the value to set for ``seed_variable``

    Returns:
        ``nbformat.NotebookNode``: the notebook with the variable substitutions made
    """
    nb = copy.deepcopy(nb)
    for cell in nb["cells"]:
        source = get_source(cell)
        for i, line in enumerate(source):
            match = re.match(fr"(\s*){seed_variable}\s*(=|<-)\s*", line)
            if  match:
                source[i] = match.group(1) + f"{seed_variable} {match.group(2)} {seed}"
        cell["source"] = "\n".join(source)
    return nb


solution_assignment_regex = re.compile(r"(\s*(?:[\w.]+(?:\[['\"].*['\"]\])*(?:,\s*)?)+\s*=).* ?# ?SOLUTION")
def solution_assignment_sub(match):
    """
    Substitutes the first matching group  with `` ...``
    """
    prefix = match.group(1)
    return prefix + ' ...'


solution_line_regex = re.compile(r"(\s*).* ?# ?SOLUTION")
def solution_line_sub(match):
    """
    Substitutes the first matching group  with ``...``
    """
    prefix = match.group(1)
    return prefix + '...'


begin_solution_regex = re.compile(r"(\s*)# BEGIN SOLUTION( NO PROMPT)?")
skip_suffixes = ['# SOLUTION NO PROMPT', '# BEGIN PROMPT', '# END PROMPT', '# SEED']

SUBSTITUTIONS = {
    "python":  [
        (solution_assignment_regex, solution_assignment_sub),
        (solution_line_regex, solution_line_sub),
    ],
    "r":  r_solutions.SUBSTITUTIONS,
}


def replace_solutions(lines, lang):
    """
    Replace solutions in ``lines``.

    Args:
        lines (``list[str]``): solutions as a list of strings
        lang (``str``): the language of the code in ``lines``

    Returns:
        ``list[str]``: stripped version of lines without solutions
    """
    if lang == "r":
        from .r_adapter.solutions import BLOCK_PROMPT
    else:
        BLOCK_PROMPT = globals()["BLOCK_PROMPT"]

    stripped = []
    solution = False
    for line in lines:

        # don't keep the line if it should be skipped
        if any(line.rstrip().endswith(s) for s in skip_suffixes):
            continue

        # don't keep the line if inside a solution block
        if solution and not line.rstrip().endswith('# END SOLUTION'):
            continue

        # process the end of a solution block
        if line.rstrip().endswith('# END SOLUTION'):
            assert solution, f"END SOLUTION without BEGIN SOLUTION in {lines}"
            solution = False
            continue

        # process the beginning of a solution block
        begin_solution = begin_solution_regex.match(line)
        if begin_solution:
            assert not solution, f"Nested BEGIN SOLUTION in {lines}"
            solution = True
            if not begin_solution.group(2):
                line = begin_solution.group(1) + BLOCK_PROMPT
            else:
                continue
        for exp, sub in SUBSTITUTIONS[lang]:
            m = exp.match(line)
            if m:
                line = sub(m)
                break

        stripped.append(line)

    assert not solution, f"BEGIN SOLUTION without END SOLUTION in {lines}"

    return stripped


def remove_ignored_lines(lines):
    """
    Remove ignored lines in ``lines``.

    Args:
        lines (``list[str]``): cell source as a list of strings

    Returns:
        ``list[str]``: stripped version of lines without ignored lines
    """
    ignore_suffix = "# IGNORE"
    stripped = []
    in_block = False
    for line in lines:

        # don't keep the line if it is ignored
        if line.rstrip().endswith(ignore_suffix):
            continue

        # don't keep the line if we're in an ignore block
        if in_block and not line.rstrip().endswith('# END IGNORE'):
            continue

        # process the end of an ignore block
        if line.rstrip().endswith('# END IGNORE'):
            assert in_block, f"END IGNORE without BEGIN IGNORE in {lines}"
            in_block = False
            continue

        # processing the beginning of an ignore block
        if re.match(r"\s*#\s*BEGIN\s*IGNORE\s*", line, flags=re.IGNORECASE):
            assert not in_block, f"Nested BEGIN IGNORE in {lines}"
            in_block = True
            continue

        stripped.append(line)

    assert not in_block, f"BEGIN IGNORE without END IGNORE in {lines}"

    return stripped


def strip_ignored_lines(nb):
    """
    Create a copy of a notebook with ignored lines stripped.

    Args:
        nb (``nbformat.NotebookNode``): the notebook to strip

    Returns:
        ``nbformat.NotebookNode``: a copy of ``nb`` with ignored line stripped
    """
    nb = copy.deepcopy(nb)
    for cell in nb['cells']:
        cell['source'] = '\n'.join(remove_ignored_lines(get_source(cell)))
    return nb


def strip_solutions_and_output(nb):
    """
    Create a copy of a notebook with solutions and outputs stripped.

    Args:
        nb (``nbformat.NotebookNode``): the notebook to strip

    Returns:
        ``nbformat.NotebookNode``: a stripped copy of ``nb``
    """
    nb = copy.deepcopy(nb)

    md_solutions = []
    lang = get_notebook_language(nb)
    for i, cell in enumerate(nb['cells']):
        if has_tag(cell, SOLUTION_CELL_TAG):
            if is_cell_type(cell, "code"):
                cell['source'] = '\n'.join(replace_solutions(get_source(cell), lang))
            elif is_cell_type(cell, "markdown"):
                md_solutions.append(i)
            nb['cells'][i] = remove_tag(cell, SOLUTION_CELL_TAG)

    md_solutions.reverse()
    for i in md_solutions:
        del nb['cells'][i]

    # remove output from student version
    remove_output(nb)

    return nb
