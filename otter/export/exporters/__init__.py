"""
Exporters for Otter Export
"""

import shutil

from .via_html import PDFViaHTMLExporter
from .via_latex import PDFViaLatexExporter

EXPORTERS = {
    "html": PDFViaHTMLExporter,
    "latex": PDFViaLatexExporter,
}

class WkhtmltopdfNotFoundError(Exception):
    """
    Exception to throw when PDF via HTML is indicated but wkhtmltopdf is not found
    """

def get_exporter(exporter_type=None):
    """
    Returns the preferred exporter to use. Defaults to PDF via LaTeX exporter. Pass a string to
    ``exporter_type`` to override this behavior.

    Args:
        exporter_type (``str``, optional): a string identifying the type of exporter to use; can be one
            of ``["html", "latex"]``

    Returns:
        ``otter.export.exporters.base_exporter.BaseExporter``: the exporter class

    Raises:
        ``WkhtmltopdfNotFoundError``: if PDF via HTML is indicated but wkhtmltopdf is not installed.
    """
    if exporter_type is not None:
        exporter_type = exporter_type.lower()
        assert exporter_type in EXPORTERS.keys(), f"{exporter_type} is not a valid PDF exporter"

        if exporter_type == 'html' and shutil.which("wkhtmltopdf") is None:
            raise WkhtmltopdfNotFoundError("PDF via HTML indicated but wkhtmltopdf not found")

        return EXPORTERS[exporter_type]

    return PDFViaLatexExporter
