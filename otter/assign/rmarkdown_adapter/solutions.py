"""
Solution removal for Otter Assign
"""

import copy
import re

from .utils import rmd_to_cells, collapse_empty_cells

from ..constants import MD_RESPONSE_CELL_SOURCE
from ..r_adapter.solutions import solution_assignment_sub, solution_line_sub
from ..utils import get_source


def is_markdown_solution_cell(cell):
    """
    Returns whether any line of the cell matches `<!-- BEGIN SOLUTION -->`
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is a Markdown solution cell
    """
    if not cell.cell_type == 'markdown':
        return False
    source = get_source(cell)
    return source and any([re.match(r"\s*<!-- BEGIN SOLUTION -->\s*", l, flags=re.IGNORECASE) for l in source])


def overwrite_seed_vars(rmd_string, seed_variable, seed):
    """
    Overwrite any assignments of the variable named ``seed_variable`` with the value ``seed`` in a
    notebook.

    Args:
        rmd_string (``str``): the Rmd document as a string
        seed_variable (``str``): the variable to look for
        seed (``int``): the value to set for ``seed_variable``

    Returns:
        ``nbformat.NotebookNode``: the notebook with the variable substitutions made
    """
    lines = rmd_string.split("\n")
    in_code_block = False
    for i, line in enumerate(lines):
        if line.startswith("```{r"):
            in_code_block = True
        elif in_code_block and line.startswith("```"):
            in_code_block = False
        elif in_code_block:
            match = re.match(fr"(\s*){seed_variable}\s*(=|<-)\s*", line)
            if match:
                lines[i] = match.group(1) + f"{seed_variable} {match.group(2)} {seed}"
    return "\n".join(lines)


solution_assignment_regex = re.compile(r"(\s*[a-zA-Z0-9_. ]*(=|<-))(.*)[ ]?#[ ]?SOLUTION")
solution_line_regex = re.compile(r"(\s*)([^#\n]+)[ ]?#[ ]?SOLUTION")

begin_solution_regex = re.compile(r"(\s*)# BEGIN SOLUTION( NO PROMPT)?")
skip_suffixes = [
    '# SOLUTION NO PROMPT', '# BEGIN PROMPT', '# END PROMPT', '# SEED', '<!-- BEGIN PROMPT -->',
    '<!-- END PROMPT -->'
]

begin_md_solution_regex = re.compile(r"(\s*)<!--\s*BEGIN SOLUTION( NO PROMPT)?\s*-->")

SUBSTITUTIONS = [
    (solution_assignment_regex, solution_assignment_sub),
    (solution_line_regex, solution_line_sub),
]


def replace_solutions(lines):
    """
    Replaces solutions in ``lines``
    
    Args:
        lines (``list`` of ``str``): solutions as a list of strings

    Returns:
        ``list`` of ``str``: stripped version of lines without solutions
    """
    stripped = []
    solution = False
    for line in lines:

        # ...
        if any(line.endswith(s) for s in skip_suffixes):
            continue

        # ...
        if solution and not (line.endswith('# END SOLUTION') or line.rstrip().endswith("<!-- END SOLUTION -->")):
            continue

        # ...
        if line.endswith('# END SOLUTION') or line.rstrip().endswith("<!-- END SOLUTION -->"):
            assert solution, f"END SOLUTION without BEGIN SOLUTION in {lines}"
            solution = False
            continue

        # ...
        begin_solution = begin_solution_regex.match(line)
        if begin_solution:
            assert not solution, f"Nested BEGIN SOLUTION in {lines}"
            solution = True
            if not begin_solution.group(2):
                line = begin_solution.group(1) + '# YOUR CODE HERE'
            else:
                continue
        
        begin_solution = begin_md_solution_regex.match(line)
        if begin_solution:
            assert not solution, f"Nested BEGIN SOLUTION in {lines}"
            solution = True
            if not begin_solution.group(2):
                line = begin_solution.group(1) + MD_RESPONSE_CELL_SOURCE
            else:
                continue
        
        for exp, sub in SUBSTITUTIONS:
            m = exp.match(line)
            if m:
                line = sub(m)
        
        stripped.append(line)
    
    assert not solution, f"BEGIN SOLUTION without END SOLUTION in {lines}"
    
    return stripped


def strip_solutions_and_output(rmd_string):
    """
    Writes a Rmd file with solutions stripped
    
    Args:
        rmd_string (``str``): the Rmd document as a string
    """
    md_solutions = []
    cells = rmd_to_cells(rmd_string)
    for i, cell in enumerate(cells):
        cell = copy.deepcopy(cells[i])
        cell["source"] = '\n'.join(replace_solutions(get_source(cell)))
        cells[i] = cell
    collapse_empty_cells(cells)
    rmd_string = "\n".join([c.source for c in cells])    
    return rmd_string
