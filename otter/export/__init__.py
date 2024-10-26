"""IPython notebook PDF Exporter forked from nb2pdf and gsExport"""

import os

from typing import Any, Optional

from .exporters import ExporterType


def export_notebook(
    nb_path: str,
    dest: Optional[str] = None,
    exporter_type: Optional[ExporterType] = None,
    **kwargs: Any,
):
    """
    Exports a notebook file at ``nb_path`` to a PDF with optional filtering and pagebreaks. Accepts
    other ``kwargs`` passed to the exporter class's ``convert_notebook`` class method.

    Args:
        nb_path (``str``): path to notebook
        dest (``str | None``): path to write PDF
        exporter_type (``"html" | "latex" | None``): the type of exporter to use
        **kwargs: additional configurations passed to exporter

    Returns:
        ``str``: the path at which the PDF was written
    """
    # If nbconvert is not installed, users should be informed that it is required for Otter Export.
    try:
        import nbconvert as _
    except:
        raise ImportError("nbconvert is required for Otter Export but it could not be found")

    from .exporters import get_exporter

    if dest is not None:
        pdf_name = dest
    else:
        pdf_name = os.path.splitext(nb_path)[0] + ".pdf"

    Exporter = get_exporter(exporter_type=exporter_type)
    Exporter.convert_notebook(nb_path, pdf_name, **kwargs)

    return pdf_name


def main(
    src: str,
    *,
    dest: Optional[str] = None,
    exporter: Optional[ExporterType] = None,
    filtering: bool = False,
    pagebreaks: bool = False,
    save: bool = False,
    xecjk: bool = False,
):
    """
    Runs Otter Export

    Args:
        src (``str``): path to source notebook
        dest (``str | None``): path at which to write PDF
        exporter (``str | None``): exporter name
        filtering (``bool``): whether to filter cells using HTML comments
        pagebreaks (``bool``): whether to pagebreak between filtered regions; ignored if ``filtering``
            is ``False``
        save (``bool``): whether to save any intermediate files (e.g. ``.tex``, ``.html``)
        xecjk (``bool``): whether to use xeCJK in the LaTeX template
    """
    export_notebook(
        src,
        dest=dest,
        exporter_type=exporter,
        filtering=filtering,
        pagebreaks=pagebreaks,
        save_tex=save,
        save_html=save,
        xecjk=xecjk,
    )
