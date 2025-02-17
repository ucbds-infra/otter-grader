"""Utilities for Otter Export exporters"""

import re


BEGIN_QUESTION_REGEX = r"<!--\s*BEGIN QUESTION\s*-->"
END_QUESTION_REGEX = r"<!--\s*END QUESTION\s*-->"
NEW_PAGE_REGEX = r"<!--\s*NEW PAGE\s*-->"
NEW_PAGE_MARKER = "#newpage"
NEW_PAGE_CELL_SOURCE = f"<!-- {NEW_PAGE_MARKER} -->"
NEW_PAGE_CLASS_NAME = "otter-page-break-after"


def has_begin(line: str) -> bool:
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


def has_end(line: str) -> bool:
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


def sub_end_for_new_page(line: str) -> str:
    """
    Substitutes an end question comment for a newpage comment

    The end question HTML comment (cf. ``otter.export.filter.has_end``) is replaced with the following
    HTML comment to indicate a pagebreak in the LaTeX template.

    .. code-block:: html

        <!-- #newpage -->

    Args:
        line (``str``): the line to substitute in

    Returns:
        ``str``: the line with the end question match substituted for the newpage comment
    """
    return re.sub(END_QUESTION_REGEX, NEW_PAGE_CELL_SOURCE, line)
