"""Utilities for Otter Run"""


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
