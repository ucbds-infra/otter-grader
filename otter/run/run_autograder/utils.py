"""Utilities for Otter Run"""

from contextlib import contextmanager
from io import StringIO
from typing import Optional


_OUTPUT: Optional[StringIO] = None
"""a StringIO object to write output to instead of stdout when it is being captured"""


class OtterRuntimeError(RuntimeError):
    """
    A an error inheriting from ``RuntimeError`` for Otter to throw during a grading process.
    """


def write_blank_page_to_stare_at_before_you(path: str):
    """
    Write a PDF file with a single blank page at the specified path.

    Args:
        path (``str``): path at which to write the PDF
    """
    from pypdf import PdfWriter

    w = PdfWriter()
    w.add_blank_page(612, 792)
    w.write(path)


@contextmanager
def capture_run_output() -> StringIO:
    """
    A context manager for capturing anything that Otter Run would normally print to stdout. Yields
    an ``io.StringIO`` object that the output will be written to.

    Yields:
        ``io.StringIO``: where the output will be written to
    """
    global _OUTPUT
    _OUTPUT = StringIO()
    yield _OUTPUT
    _OUTPUT = None


def print_output(*args, **kwargs):
    """
    Print output for Otter Run. If output is being captured, this prints the output to the
    ``io.StringIO`` object it is being captured to, otherwise it prints to stdout. All arguments are
    passed to ``print``.
    """
    print(*args, **kwargs, file=_OUTPUT)
