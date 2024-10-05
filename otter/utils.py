"""Various utilities for Otter-Grader"""

import nbformat
import os
import pathlib
import random
import re
import shutil
import string
import tempfile
import traceback
import yaml

from collections.abc import Generator
from contextlib import contextmanager
from IPython.core.getipython import get_ipython
from typing import Any, Optional


NBFORMAT_VERSION = 4
"""the version of the Jupyter notebook format to use"""

NOTEBOOK_METADATA_KEY = "otter"
"""the key used for all Otter metadata added to a notebook"""

REQUIRE_CONFIRMATION_NO_PDF_EXPORT_KEY = "require_no_pdf_confirmation"
"""
the key in Otter's notebook metadata for requiring students to acknowledge that their notebook could
not be exported as a PDF before creating the submission zip file
"""

NO_PDF_EXPORT_MESSAGE_KEY = "export_pdf_failure_message"
"""
the key in Otter's notebook metadata for the message to show if a notebook cannot be exported as a
PDF
"""

OTTER_CONFIG_FILENAME = "otter_config.json"
"""the file name for the autograder config JSON file"""


@contextmanager
def hide_outputs():
    """
    Context manager for hiding outputs from ``display()`` calls. IPython handles matplotlib outputs
    specially, so those are supressed too.
    """
    ipy = get_ipython()
    if ipy is None:
        # Not running inside ipython!
        yield
        return
    old_formatters = ipy.display_formatter.formatters
    ipy.display_formatter.formatters = {}
    try:
        yield
    finally:
        ipy.display_formatter.formatters = old_formatters


def id_generator(size: int = 6, chars: str = string.ascii_uppercase + string.digits) -> str:
    """
    Used to generate a dynamic variable name for grading functions

    This function generates a random name using the given length and character set.

    Args:
        size (``int``): length of output name
        chars (``str``): set of characters used to create function name

    Returns:
        ``str``: randomized string name for grading function
    """
    return "".join(random.choice(chars) for _ in range(size))


def get_variable_type(obj: Any) -> str:
    """
    Returns the fully-qualified type string of an object ``obj``

    Args:
        obj (any): the object in question

    Returns:
        ``str``: the fully-qualified type string
    """
    return type(obj).__module__ + "." + type(obj).__name__


def get_relpath(src: pathlib.Path, dst: pathlib.Path) -> pathlib.Path:
    """
    Returns the relative path from ``src`` to ``dst``

    Args:
        src (``pathlib.Path``): the source directory
        dst (``pathlib.Path``): the destination directory

    Returns:
        ``pathlib.Path``: the relative path
    """
    ups = 0
    while True:
        try:
            dst.relative_to(src)
            break
        except ValueError:
            src = src.parent
            ups += 1
    return pathlib.Path(("../" * ups) / dst.relative_to(src))


@contextmanager
def chdir(new_dir: "os.PathLike[Any]"):
    """
    Create a context with a different working directory, resetting the working directory on exit.

    Args:
        new_dir (path-like): the directory for the context
    """
    curr_dir = os.getcwd()
    os.chdir(new_dir)

    try:
        yield

    finally:
        os.chdir(curr_dir)


def get_source(cell: nbformat.NotebookNode) -> list[str]:
    """
    Returns the source code of a cell in a way that works for both nbformat and JSON

    Args:
        cell (``nbformat.NotebookNode``): notebook cell

    Returns:
        ``list[str]``: each line of the cell source stripped of ending line breaks
    """
    source = cell.source
    if isinstance(source, str):
        return re.split("\r?\n", source)
    elif isinstance(source, list):
        return [line.strip("\r\n") for line in source]
    raise TypeError(f"Unknown cell source type: {type(source)}")


@contextmanager
def load_default_file(
    provided_filename: Optional[str], default_filename: str, default_disabled: bool = False
) -> Generator[Optional[str]]:
    """
    Reads the contents of a file with an optional default path. If ``provided_filename`` is not specified
    and ``default_filename`` is an existing file path, the contents of ``default_filename`` are read in place
    of ``provided_filename``. The use of ``default_filename`` can be disabled by setting ``default_disabled``
    to ``True``.
    """
    if provided_filename is None and os.path.isfile(default_filename) and not default_disabled:
        provided_filename = default_filename

    if provided_filename is not None:
        if not os.path.isfile(provided_filename):
            raise FileNotFoundError(f"Could not find specified file: {provided_filename}")

        with open(provided_filename) as f:
            yield f.read()

    else:
        yield


def format_full_width(char: str, mid_text: str = "", whitespace: str = " ") -> str:
    """
    Format a character at the full terminal width. If ``mid_text`` is supplied, this text is printed
    in the middle of the terminal, surrounded by ``whitespace``.
    """
    cols, _ = shutil.get_terminal_size()

    if mid_text:
        left = cols - len(mid_text) - 2 * len(whitespace)
        if left <= 0:
            left = 2
        l, r = left // 2, left // 2
        if left % 2 == 1:
            r += 1

        out = char * l + whitespace + mid_text + whitespace + char * r

    else:
        out = char * cols

    return out


def print_full_width(char: str, mid_text: str = "", whitespace: str = " ", **kwargs: Any):
    """
    Prints a character at the full terminal width. Additional kwargs passed to ``print``.

    See ``format_full_width`` for details on the named arguments.
    """
    print(format_full_width(char, mid_text, whitespace), **kwargs)


def assert_path_exists(path_tuples: list[tuple[str, bool]]):
    """
    Ensure that a series of file paths exist and are of a specific type, or raise a ``ValueError``.

    Elements of ``path_tuples`` should be 2-tuples where the first element is a string representing
    the file path and the second element is ``True`` if the path should be a directory, ``False`` if
    it should be a file, and ``None`` if it doesn't matter.

    Args:
        path_tuples (``list[tuple[str, bool]]``): the list of paths as described above

    Raises:
        ``FileNotFoundError``: if the path does not exist or it is not of the correct type
    """
    for path, is_dir in path_tuples:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} does not exist")
        if is_dir and not os.path.isdir(path):
            raise FileNotFoundError(f"Path {path} is not a directory")
        if is_dir is False and not os.path.isfile(path):
            raise FileNotFoundError(f"Path {path} is not a file")


def knit_rmd_file(rmd_path: str, pdf_path: str):
    """
    Use ``rpy2`` and ``rmarkdown::render`` to knit an RMarkdown file to a PDF, allowing errors.

    Args:
        rmd_path (``str``): the path to the Rmd file
        pdf_path (``str``): the path at which to write the PDF
    """
    from rpy2.robjects.packages import importr

    with tempfile.NamedTemporaryFile(mode="w", suffix=".Rmd") as ntf:
        with open(rmd_path) as f:
            contents = f.read()

        contents = (
            "```{r cache = F, include = F}\nknitr::opts_chunk$set(error = TRUE)\n```\n" + contents
        )
        ntf.write(contents)
        ntf.seek(0)

        pdf_path = os.path.abspath(pdf_path)
        rmarkdown = importr("rmarkdown")
        rmarkdown.render(ntf.name, "pdf_document", pdf_path)


class _CorrectIndentationDumper(yaml.Dumper):
    def increase_indent(self, flow: bool = False, *args: Any, **kwargs: Any):
        return super().increase_indent(flow=flow, indentless=False)


def dump_yaml(o: Any, **kwargs: Any) -> str:
    """
    Dump an object to a YAML string using the ``_CorrectIndentationDumper`` dumper.

    Args:
        o (``object``): the object to dump
        **kwargs: additional keyword arguments passed to ``yaml.dump``

    Returns:
        ``str``: the YAML representation of ``o``
    """
    return yaml.dump(o, sort_keys=False, Dumper=_CorrectIndentationDumper, **kwargs)


class QuestionNotInLogException(Exception):
    """
    Exception that indicates that a specific question was not found in any entry in the log
    """


def format_exception(e: Exception) -> str:
    """
    Formats an exception for display with its traceback using the ``traceback`` module.

    Args:
        e (``Exception``): the exception to format

    Returns:
        ``str``: the formatted exception
    """
    return "".join(traceback.format_exception(type(e), e, e.__traceback__))
