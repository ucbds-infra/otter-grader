"""
Cell filtering for IPython notebook exports forked from nb2pdf and gsExport
"""

import re
import nbformat

NBFORMAT_VERSION = 4
BEGIN_QUESTION_REGEX = r"<!--\s*BEGIN QUESTION\s*-->"
END_QUESTION_REGEX = r"<!--\s*END QUESTION\s*-->"
NEW_PAGE_REGEX = r"<!--\s*NEW PAGE\s*-->"
NEW_PAGE_CELL_SOURCE = "<!-- #newpage -->"

def load_notebook(nb_path, filtering=True, pagebreaks=False):
    """
    Loads notebook at ``nb_path`` with nbformat and returns the parsed notebook, optionally filtered
    and with pagebreak metadata hidden in HTML comments.

    Args:
        nb_path (``str``): path to notebook
        filtering (``bool``, optional): whetheer cells should be filtered
        pagebreaks (``bool``, optional): whether to include pagebreaks between each question; ignored
            if ``filtering`` is ``False``

    Returns:
        ``nbformat.NotebookNode``: the parsed and (optionally) filtered notebook
    """
    with open(nb_path) as f:
        notebook = nbformat.read(f, as_version=NBFORMAT_VERSION)
    if filtering:
        notebook = filter_notebook_cells_by_comments(notebook, pagebreaks=pagebreaks)
    return notebook

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

def filter_notebook_cells_by_comments(notebook, pagebreaks=False):
    """
    Filters a parsed notebook using HTML comments in Markdown cells. Optionally inserts pagebreak
    metadata as HTML comments.

    Args:
        notebook (``nbformat.NotebookNode``): the parsed notebook
        pagebreaks (``bool``, optional): whether to include pagebreaks between questions

    Returns:
        ``nbformat.NotebookNode``: the filtered notebook with (optional) pagebreaks
    """
    cells = notebook["cells"]

    idx_to_delete, in_question = [], False
    for curr_idx, cell in enumerate(cells):

        if isinstance(cell["source"], str):
            source = cell["source"].split("\n")
        elif isinstance(cell["source"], list):
            source = [line.strip("\n") for line in cell["source"]]
        else:
            raise Exception("Invalid notebook cell source: {}".format(cell))

        lines_before_begin, lines_after_end = -1, -1
        for line_idx, line in enumerate(source):

            # check for begin question regex in source
            if not in_question:
                if has_begin(line) and lines_before_begin == -1:
                    lines_before_begin = line_idx
                    in_question = True
            
            # check for end question regex in source
            else:
                if has_end(line):
                    lines_after_end = line_idx
                    in_question = False
                    
                    # if we are creating pagebreaks, sub the end regex for a newpage directive
                    if pagebreaks:
                        source[line_idx] = sub_end_for_new_page(line)

        # if we are not in question and there is no begin/end comment, delete the cell
        if lines_before_begin == -1 and lines_after_end == -1 and not in_question:
            idx_to_delete.append(curr_idx)

        # if both are in cell and before is after end, delete intervening lines
        elif lines_before_begin != -1 and lines_after_end != -1 and lines_after_end < lines_before_begin:
            del source[lines_after_end+1:lines_before_begin]
        
        else:
            # if there is an end comment, delete lines after that
            if lines_after_end != -1:
                del source[lines_after_end+1:]

            # if there is a begin comment, delete lines before that
            if lines_before_begin != -1:
                del source[:lines_before_begin]

        # update source
        cell["source"] = "\n".join(source)
    
    # reverse indices list so that we do not need to decrement while deleting
    idx_to_delete.reverse()

    # delete at indices
    for idx in idx_to_delete:
        del cells[idx]

    return notebook
