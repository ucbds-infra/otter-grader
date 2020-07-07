import re


from .defaults import SEED_REGEX, MD_SOLUTION_REGEX, SOLUTION_REGEX, BLOCK_QUOTE

class EmptyCellException(Exception):
    """Exception for empty cells to indicate deletion"""


#---------------------------------------------------------------------------------------------------
# Getters
#---------------------------------------------------------------------------------------------------

def get_source(cell):
    """Get the source code of a cell in a way that works for both nbformat and JSON
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``list`` of ``str``: each line of the cell source
    """
    source = cell['source']
    if isinstance(source, str):
        return cell['source'].split('\n')
    elif isinstance(source, list):
        return [line.strip('\n') for line in source]
    assert 'unknown source type', type(source)

def get_spec(source, begin):
    """Return line number of the BEGIN ASSIGNMENT line or None
    
    Args:
        source (``list`` of ``str``): cell source as a list of lines of text
    
    Returns:
        ``int``: line number of BEGIN ASSIGNMENT, if present
        ``None``: if BEGIN ASSIGNMENT not present in the cell
    """
    block_quotes = [
        i for i, line in enumerate(source) if line[:3] == BLOCK_QUOTE
    ]
    assert len(block_quotes) % 2 == 0, f"wrong number of block quote delimieters in {source}"

    begins = [
        block_quotes[i] + 1 for i in range(0, len(block_quotes), 2) 
        if source[block_quotes[i]+1].strip(' ') == f"BEGIN {begin.upper()}"
    ]
    assert len(begins) <= 1, f'multiple BEGIN blocks defined in {source}'
    
    return begins[0] if begins else None

# TODO: update these
#---------------------------------------------------------------------------------------------------
# Cell Type Checkers
#---------------------------------------------------------------------------------------------------

def is_seed_cell(cell):
    """Whether cell is seed cell
    
    Args:
        cell (``nbformat.NotebookNode``): notebook cell
    
    Returns:
        ``bool``: whether the current cell is a seed cell
    """
    if cell['cell_type'] != 'code':
        return False
    source = get_source(cell)
    return source and SEED_REGEX.match(source[0], flags=re.IGNORECASE)

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


#---------------------------------------------------------------------------------------------------
# Cell Reformatters
#---------------------------------------------------------------------------------------------------

def remove_output(nb):
    """Remove all outputs from a notebook
    
    Args:
        nb (``nbformat.NotebookNode``): a notebook
    """
    for cell in nb['cells']:
        if 'outputs' in cell:
            cell['outputs'] = []

def lock(cell):
    """Makes a cell non-editable and non-deletable

    Args:
        cell (``nbformat.NotebookNode``): cell to be locked
    """
    m = cell['metadata']
    m["editable"] = False
    m["deletable"] = False
