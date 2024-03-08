"""Exporters for Otter Export"""

import shutil

from .via_html import PDFViaHTMLExporter
from .via_latex import PDFViaLatexExporter


def get_exporter(exporter_type=None):
    """
    Returns the preferred exporter to use. Defaults to PDF via LaTeX exporter. Pass a string to
    ``exporter_type`` to override this behavior.

    Args:
        exporter_type (``str``, optional): a string identifying the type of exporter to use; can be one
            of ``["html", "latex"]``

    Returns:
        ``otter.export.exporters.base_exporter.BaseExporter``: the exporter class
    """
    # throw an error if the nbconvert version is < 6
    import nbconvert
    if int(nbconvert.__version__.split(".")[0]) < 6:
        raise RuntimeError(f"Otter is only compatible with nbconvert>=6.0.0, found {nbconvert.__version__}")

    if exporter_type is not None:
        exporter_type = exporter_type.lower()

        if exporter_type == 'html':
            return PDFViaHTMLExporter

        elif exporter_type == "latex":
            return PDFViaLatexExporter

        else:
            raise ValueError(f"{exporter_type} is not a valid PDF exporter")

    return PDFViaLatexExporter
