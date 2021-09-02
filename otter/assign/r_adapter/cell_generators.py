"""Cell generators for R notebooks"""

import nbformat

from ..utils import lock


def gen_export_cells(nb_name, instruction_text):
    """
    Generates export cells that instruct the student the run a code cell calling 
    ``ottr::export`` to generate and download their submission. The Markdown cell contains:

    .. code-block:: markdown

        ## Submission
        
        Make sure you have run all cells in your notebook in order before running the cell below, so 
        that all images/graphs appear in the output. The cell below will generate a zipfile for you 
        to submit. **Please save before exporting!**

    Additional instructions can be appended to this cell by passing a string to ``instruction_text``.

    The code cell contains:

    .. code-block:: python

        # Save your notebook first, then run this cell to export your submission.
        ottr::export("path/to/notebook.ipynb")
    
    Args:
        instruction_text (``str``): extra instructions for students when exporting
        **kwargs: a catch-all so that the API matches 
            ``otter.assign.cell_generators.gen_export_cells``
    
    Returns:
        ``list`` of ``nbformat.NotebookNode``: generated export cells
    """
    instructions = nbformat.v4.new_markdown_cell()
    instructions.source = "## Submission\n\nMake sure you have run all cells in your notebook in order before " \
    "running the cell below, so that all images/graphs appear in the output. The cell below will generate " \
    "a zip file for you to submit. **Please save before exporting!**"
    
    if instruction_text:
        instructions.source += '\n\n' + instruction_text

    export = nbformat.v4.new_code_cell()
    source_lines = ["# Save your notebook first, then run this cell to export your submission."]
    source_lines.append(f'ottr::export("{nb_name}")')
    export.source = "\n".join(source_lines)

    lock(instructions)
    lock(export)

    return [instructions, export, nbformat.v4.new_markdown_cell(" ")]     # last cell is buffer
