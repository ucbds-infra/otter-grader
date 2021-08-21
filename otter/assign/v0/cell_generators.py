"""
Miscellaneous cell generators for Otter Assign
"""

import copy
import nbformat

from .constants import MD_RESPONSE_CELL_SOURCE
from .utils import get_source, lock

def gen_init_cell(nb_name, colab):
    """
    Generates a cell to initialize Otter in the notebook.

    Args:
        nb_name (``str``): the name of the notebook being graded
        colab (``bool``): whether the notebook will be run on Colab
    
    Returns:
        ``nbformat.NotebookNode``: the init cell
    """
    if colab:
        args = "colab=True"
    else:
        args  = f"\"{nb_name}\""
    contents = f'# Initialize Otter\nimport otter\ngrader = otter.Notebook({args})'
    cell = nbformat.v4.new_code_cell(contents)
    lock(cell)
    return cell

def gen_markdown_response_cell():
    """
    Generates a Markdown response cell with the following contents:

    .. code-block:: markdown

        _Type your answer here, replacing this text._

    Returns:
        ``nbformat.NotebookNode``: the response cell
    """
    return nbformat.v4.new_markdown_cell(MD_RESPONSE_CELL_SOURCE)

def gen_export_cells(instruction_text, pdf=True, filtering=True, force_save=False, run_tests=False):
    """
    Generates export cells that instruct the student the run a code cell calling 
    ``otter.Notebook.export`` to generate and download their submission. The Markdown cell contains:

    .. code-block:: markdown

        ## Submission
        
        Make sure you have run all cells in your notebook in order before running the cell below, so 
        that all images/graphs appear in the output. The cell below will generate a zipfile for you 
        to submit. **Please save before exporting!**

    Additional instructions can be appended to this cell by passing a string to ``instruction_text``.

    The code cell contains:

    .. code-block:: python

        # Save your notebook first, then run this cell to export your submission.
        grader.export()
    
    The call to ``grader.export()`` contains different arguments based on the values passed to ``pdf``
    and ``filtering``. 
    
    Args:
        instruction_text (``str``): extra instructions for students when exporting
        pdf (``bool``, optional): whether a PDF is needed
        filtering (``bool``, optional): whether PDF filtering is needed
        force_save (``bool``, optional): whether or not to set the ``force_save`` argument of 
            ``otter.Notebook.export`` to ``True``
        run_tests (``bool``, optional): whether to set the ``run_tests`` argument of 
            ``otter.Notebook.export`` to ``True``
    
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
    args = []
    if not filtering:
        args += ["filtering=False"]
    elif not pdf:
        args += ["pdf=False"]
    if force_save:
        args += ["force_save=True"]
    if run_tests:
        args += ["run_tests=True"]

    source_lines.append(f"grader.export({', '.join(args)})")
    export.source = "\n".join(source_lines)

    lock(instructions)
    lock(export)

    return [instructions, export, nbformat.v4.new_markdown_cell(" ")]     # last cell is buffer

def gen_check_all_cell():
    """
    Generates a check-all cell and a Markdown cell with instructions to run all tests in the notebook. 
    The Markdown cell has the following contents:

    .. code-block:: markdown

        ---
        
        To double-check your work, the cell below will rerun all of the autograder tests.

    The code cell has the following contents:

    .. code-block:: python

        grader.check_all()
    
    Returns:
        ``list`` of ``nbformat.NotebookNode``: generated check-all cells
    """
    instructions = nbformat.v4.new_markdown_cell()
    instructions.source = "---\n\nTo double-check your work, the cell below will rerun all of the autograder tests."

    check_all = nbformat.v4.new_code_cell("grader.check_all()")

    lock(instructions)
    lock(check_all)

    return [instructions, check_all]

def gen_close_export_cell():
    """
    Generates a Markdown cell to end question export for PDF filtering. The cell contains:

    .. code-block:: markdown

        <!-- END QUESTION -->
    
    Returns:
        ``nbformat.NotebookNode``: new Markdown cell with ``<!-- END QUESTION -->``
    """
    cell = nbformat.v4.new_markdown_cell("<!-- END QUESTION -->")
    lock(cell)
    return cell

def add_close_export_to_cell(cell):
    """
    Adds an HTML comment to close question export for PDF filtering to the top of ``cell``. ``cell``
    should be a Markdown cell. This adds ``<!-- END QUESTION-->`` as the first line of the cell.
    
    Args:
        cell (``nbformat.NotebookNode``): the cell to add the close export to

    Returns:
        ``nbformat.NotebookNode``: the cell with the close export comment at the top
    """
    cell = copy.deepcopy(cell)
    source = get_source(cell)
    source = ["<!-- END QUESTION -->\n", "\n"] + source
    cell['source'] = "\n".join(source)
    return cell

