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

def get_exporter(exporter_type=None):
    """
    Returns the preferred exporter to use. Defaults to PDF via HTML exporter if wkhtmltopdf is installed
    (found using ``shutil.which``) and otherwise returns PDF via LaTeX exporter. Pass a string to
    ``exporter_type`` to override this behavior.

    Args:
        exporter_type (``str``, optional): a string identifying the type of exporter to use; can be one
            of `("html", "latex")`

    Returns:
        ``otter.export.exporters.base_exporter.BaseExporter``: the exporter class
    """
    if exporter_type is not None:
        exporter_type = exporter_type.lower()
        assert exporter_type in EXPORTERS.keys(), f"{exporter_type} is not a valid PDF exporter"
        return EXPORTERS[exporter_type]

    if shutil.which("wkhtmltopdf") is not None:
        return PDFViaHTMLExporter

    return PDFViaLatexExporter
