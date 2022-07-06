"""Utilities for Otter Export exporters"""

import re
import copy
import nbformat

from ...utils import get_source


BEGIN_QUESTION_REGEX = r"<!--\s*BEGIN QUESTION\s*-->"
END_QUESTION_REGEX = r"<!--\s*END QUESTION\s*-->"
NEW_PAGE_REGEX = r"<!--\s*NEW PAGE\s*-->"
NEW_PAGE_MARKER = "#newpage"
NEW_PAGE_CELL_SOURCE = f"<!-- {NEW_PAGE_MARKER} -->"
NEW_PAGE_CLASS_NAME = "otter-page-break-after"


def has_begin(line):
    """
    Returns whether a string contains a begin question comment

    A begin question comment is an HTML comment on a single line that denotes the beginning of an 
    export block. The begin question comment looks like:

    .. code-block:: html

        <!-- BEGIN QUESTION -->

    Args:
        line (``str``): the line to search

    Returns:
        ``bool``: whether the line contains a substring matching the begin question regex
    """
    return bool(re.search(BEGIN_QUESTION_REGEX, line, flags=re.IGNORECASE))


def has_end(line):
    """
    Returns whether a string contains an end question comment

    An end question comment is an HTML comment on a single line that denotes the end of an export 
    block. The begin question comment looks like:

    .. code-block:: html

        <!-- END QUESTION -->

    Args:
        line (``str``): the line to search

    Returns:
        ``bool``: whether the line contains a substring matching the end question regex
    """
    return bool(re.search(END_QUESTION_REGEX, line, flags=re.IGNORECASE))


def sub_end_for_new_page(line):
    """
    Subsitutes an end question comment for a newpage comment

    The end question HTML comment (cf. ``otter.export.filter.has_end``) is replaced with the following
    HTML comment to indicate a pagebreak in the LaTeX template.

    .. code-block:: html

        <!-- #newpage -->

    Args:
        ``line``: the line to substitute in

    Returns:
        ``str``: the line with the end question match substituted for the newpage comment
    """
    return re.sub(END_QUESTION_REGEX, NEW_PAGE_CELL_SOURCE, line)


def notebook_pdf_generator(nb):
    """
    A generator that takes in a notebook ``nb`` with HTML comments for filtering and splits this
    notebook up into each filtered block, yielding a complete notebook for each chunk. Used for 
    implementing pagebreaks in PDFs via HTML.

    Args:
        nb (``nbformat.NotebookNode``): the notebook to be exported

    Yields:
        ``nbformat.NotebookNode``: a complete notebook containing a single filtered block
    """
    dummy_nb = copy.copy(nb)
    dummy_nb.cells = []

    all_cells, subnb_cells = [], []
    for cell in nb.cells:
        source = get_source(cell)

        if NEW_PAGE_CELL_SOURCE in "\n".join(source):
            for i, line in enumerate(source):
                if NEW_PAGE_CELL_SOURCE in line:
                    break

            c1, c2 = nbformat.v4.new_markdown_cell(), nbformat.v4.new_markdown_cell()
            c1.source, c2.source = "\n".join(source[:i+1]), "\n".join(source[i+1:])

            subnb_cells.append(c1)
            all_cells.append(subnb_cells)
            subnb_cells = []
            subnb_cells.append(c2)

        else:
            subnb_cells.append(cell)

    all_cells.append(subnb_cells)

    for subnb_cells in all_cells:
        dummy_nb.cells = subnb_cells
        yield dummy_nb
