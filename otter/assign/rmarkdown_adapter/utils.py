from collections import namedtuple

Cell = namedtuple("Cell", ["cell_type", "source"])

def rmd_to_cells(rmd_string):
    """
    Converts an Rmd document as a string into a list of ``Cell`` objects for easier handling with
    code designed originally for Jupyter notebooks.

    Args:
        rmd_string (``str``): the Rmd document as a string

    Returns:
        ``list`` of ``Cell``: the "cells" represented named tuples
    """
    cells, cell_lines, in_block = [], [], False
    for line in rmd_string.split("\n"):
        if line.startswith("```{r") and line.strip().endswith("}"):
            in_block = True

            # collect cell_lines into a new Cell
            cells.append(Cell("markdown", "\n".join(cell_lines)))
            cell_lines = [line]
        
        elif in_block and line.strip() == "```":
            in_block = False

            # collect cell_lines into a new Cell
            cells.append(Cell("code", "\n".join(cell_lines + [line])))
            cell_lines = []
        
        else:
            cell_lines.append(line)

    # collect remaining cell lines into a new Cell
    if cell_lines:
        cells.append(Cell("code", "\n".join(cell_lines)))

    return cells
