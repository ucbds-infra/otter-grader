"""Exporters for Otter Export"""

import shutil

from .via_latex import PDFViaLatexExporter

from ..utils import WkhtmltopdfNotFoundError


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

        if exporter_type == 'html':
            if shutil.which("wkhtmltopdf") is None:
                raise WkhtmltopdfNotFoundError("PDF via HTML indicated but wkhtmltopdf not found")

            from .via_html import PDFViaHTMLExporter
            return PDFViaHTMLExporter

        elif exporter_type == "latex":
            return PDFViaLatexExporter

        else:
            raise ValueError(f"{exporter_type} is not a valid PDF exporter")

    return PDFViaLatexExporter
