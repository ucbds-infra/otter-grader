"""Exporters for Otter Export"""

from typing import Literal, Optional, Union

from .base_exporter import BaseExporter
from .via_html import PDFViaHTMLExporter
from .via_latex import PDFViaLatexExporter


ExporterType = Union[Literal["html"], Literal["latex"]]


def get_exporter(exporter_type: Optional[ExporterType] = None) -> type[BaseExporter]:
    """
    Returns the preferred exporter to use. Defaults to PDF via LaTeX exporter. Pass a string to
    ``exporter_type`` to override this behavior.

    Args:
        exporter_type (``"html" | "latex" | None``): a string identifying the type of exporter to
            use; can be one of ``["html", "latex"]``

    Returns:
        ``type[otter.export.exporters.base_exporter.BaseExporter]``: the exporter class
    """
    # throw an error if the nbconvert version is < 6
    import nbconvert

    if int(nbconvert.__version__.split(".")[0]) < 6:
        raise RuntimeError(
            f"Otter is only compatible with nbconvert>=6.0.0, found {nbconvert.__version__}"
        )

    if exporter_type is not None:
        exporter_type = exporter_type.lower()

        if exporter_type == "html":
            return PDFViaHTMLExporter

        elif exporter_type == "latex":
            return PDFViaLatexExporter

        else:
            raise ValueError(f"{exporter_type} is not a valid PDF exporter")

    return PDFViaLatexExporter
