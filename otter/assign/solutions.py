import re
import nbformat

from .defaults import NB_VERSION, MD_SOLUTION_REGEX, SOLUTION_REGEX
from .utils import get_source, is_markdown_solution_cell, remove_output

# TODO: are these needed??
def is_markdown_solution_cell(cell):
    """Whether the cell matches MD_SOLUTION_REGEX
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is a Markdown solution cell
    """
    source = get_source(cell)
    return is_solution_cell and any([MD_SOLUTION_REGEX.match(l, flags=re.IGNORECASE) for l in source])

def is_solution_cell(cell):
    """Whether the cell matches SOLUTION_REGEX or MD_SOLUTION_REGEX
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is a solution cell
    """
    source = get_source(cell)
    if cell['cell_type'] == 'markdown':
        return source and any([MD_SOLUTION_REGEX.match(l, flags=re.IGNORECASE) for l in source])
    elif cell['cell_type'] == 'code':
        return source and SOLUTION_REGEX.match(source[0], flags=re.IGNORECASE)
    return False

solution_assignment_regex = re.compile(r"(\s*[a-zA-Z0-9_ ]*=)(.*)[ ]?#[ ]?SOLUTION")
def solution_assignment_sub(match):
    prefix = match.group(1)
    return prefix + ' ...'

solution_line_regex = re.compile(r"(\s*)([^#\n]+)[ ]?#[ ]?SOLUTION")
def solution_line_sub(match):
    prefix = match.group(1)
    return prefix + '...'

begin_solution_regex = re.compile(r"(\s*)# BEGIN SOLUTION( NO PROMPT)?")
skip_suffixes = ['# SOLUTION NO PROMPT', '# BEGIN PROMPT', '# END PROMPT']

SUBSTITUTIONS = [
    (solution_assignment_regex, solution_assignment_sub),
    (solution_line_regex, solution_line_sub),
]

# TODO: comments
def replace_solutions(lines):
    """Replace solutions in lines, a list of strings
    
    Args:
        lines (``list`` of ``str``): solutions as a list of strings

    Returns:
        ``list`` of ``str``: stripped version of lines without solutions
    """
    stripped = []
    solution = False
    for line in lines:
        line = line.strip()

        # ...
        if any(line.endswith(s) for s in skip_suffixes):
            continue

        # ...
        if solution and not line.endswith('# END SOLUTION'):
            continue

        # ...
        if line.endswith('# END SOLUTION'):
            assert solution, f"END SOLUTION without BEGIN SOLUTION in {lines}"
            solution = False
            continue

        # ...
        begin_solution = begin_solution_regex.match(line)
        if begin_solution:
            assert not solution, f"Nested BEGIN SOLUTION in {lines}"
            solution = True
            if not begin_solution.group(2):
                line = begin_solution.group(1) + '...'
            else:
                continue
        for exp, sub in SUBSTITUTIONS:
            m = exp.match(line)
            if m:
                line = sub(m)
        
        stripped.append(line)
    
    assert not solution, f"BEGIN SOLUTION without END SOLUTION in {lines}"
    
    return stripped

# TODO: make this _not_ write files
def strip_solutions(original_nb_path, stripped_nb_path):
    """Write a notebook with solutions stripped
    
    Args:
        original_nb_path (path-like): path to original notebook
        stripped_nb_path (path-like): path to new stripped notebook
    """
    with open(original_nb_path) as f:
        nb = nbformat.read(f, NB_VERSION)
    md_solutions = []
    for i, cell in enumerate(nb['cells']):
        cell['source'] = '\n'.join(replace_solutions(get_source(cell)))
        if is_markdown_solution_cell(cell):
            md_solutions.append(i)
    md_solutions.reverse()
    for i in md_solutions:
        del nb['cells'][i]
    
    # remove output from student version
    remove_output(nb)
    with open(stripped_nb_path, 'w') as f:
        nbformat.write(nb, f, NB_VERSION)
