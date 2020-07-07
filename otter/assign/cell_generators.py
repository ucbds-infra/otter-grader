import nbformat

def gen_init_cell():
    """Generates a cell to initialize Otter in the notebook
    
    Returns:
        cell (``nbformat.NotebookNode``): new code cell
    """
    cell = nbformat.v4.new_code_cell("# Initialize Otter\nimport otter\ngrader = otter.Notebook()")
    lock(cell)
    return cell

def gen_export_cells(instruction_text, pdf=True, filtering=True):
    """Generates export cells
    
    Args:
        instruction_text (``str``): extra instructions for students when exporting
        pdf (``bool``, optional): whether a PDF is needed
        filtering (``bool``, optional): whether PDF filtering is needed
    
    Returns:
        ``list`` of ``nbformat.NotebookNode``: generated export cells

    """
    instructions = nbformat.v4.new_markdown_cell()
    instructions.source = "## Submission\n\nMake sure you have run all cells in your notebook in order before \
    running the cell below, so that all images/graphs appear in the output. The cell below will generate \
    a zipfile for you to submit. **Please save before exporting!**"
    
    if instruction_text:
        instructions.source += '\n\n' + instruction_text

    export = nbformat.v4.new_code_cell()
    source_lines = ["# Save your notebook first, then run this cell to export your submission."]
    if filtering and pdf:
        source_lines.append(f"grader.export()")
    elif not filtering:
        source_lines.append(f"grader.export(filtering=False)")
    else:
        source_lines.append(f"grader.export(pdf=False)")
    export.source = "\n".join(source_lines)

    lock(instructions)
    lock(export)

    return [instructions, export, nbformat.v4.new_markdown_cell(" ")]     # last cell is buffer

def gen_check_all_cell():
    """Generates an ``otter.Notebook.check_all`` cell
    
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
    """Returns a new cell to end question export
    
    Returns:
        ``nbformat.NotebookNode``: new Markdown cell with ``<!-- END QUESTION -->``
    """
    cell = nbformat.v4.new_markdown_cell("<!-- END QUESTION -->")
    lock(cell)
    return cell


def add_close_export_to_cell(cell):
    """Adds an export close to the top of the cell. Mutates the original cell
    
    Args:
        cell (``nbformat.NotebookNode``): the cell to add the close export to
    """
    source = get_source(cell)
    source = ["<!-- END QUESTION -->\n", "\n"] + source
    cell['source'] = "\n".join(source)

