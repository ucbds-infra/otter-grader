"""IPython notebook PDF Exporter forked from nb2pdf and gsExport"""

import os

from .utils import WkhtmltopdfNotFoundError


# TODO: convert to import_or_raise?
# check for nbconvert and disable otter.export if it's not installed -- #458
_MISSING_NBCONVERT = False
try:
    import nbconvert
except ImportError:
    _MISSING_NBCONVERT = True


def export_notebook(nb_path, dest=None, exporter_type=None, **kwargs):
    """
    Exports a notebook file at ``nb_path`` to a PDF with optional filtering and pagebreaks. Accepts
    other ``kwargs`` passed to the exporter class's ``convert_notebook`` class method.

    Args:
        nb_path (``str``): path to notebook
        dest (``str``, optional): path to write PDF
        exporter_type (``str``, optional): the type of exporter to use; one of ``['html', 'latex']``
        **kwargs: additional configurations passed to exporter

    Returns:
        ``str``: the path at which the PDF was written
    """
    if _MISSING_NBCONVERT:
        raise ImportError("nbconvert is required for Otter Export but it could not be found")

    from .exporters import get_exporter

    if dest is not None:
        pdf_name = dest
    else:
        pdf_name = os.path.splitext(nb_path)[0] + ".pdf"

    Exporter = get_exporter(exporter_type=exporter_type)
    Exporter.convert_notebook(nb_path, pdf_name, **kwargs)

    return pdf_name


def main(src, *, dest=None, exporter=None, filtering=False, pagebreaks=False, save=False, 
         xecjk=False):
    """
    Runs Otter Export

    Args:
        src (``str``): path to source notebook
        dest (``Optional[str]``): path at which to write PDF
        exporter (``Optional[str]``): exporter name
        filtering (``bool``): whether to filter cells using HTML comments
        pagebreaks (``bool``): whether to pagebreak between filtered regions; ignored if ``filtering``
            is ``False``
        save (``bool``): whether to save any intermediate files (e.g. ``.tex``, ``.html``)
        xecjk (``bool``): whether to use xeCJK in the LaTeX template
    """
    export_notebook(
        src,
        dest = dest,
        exporter_type = exporter,
        filtering = filtering,
        pagebreaks = pagebreaks,
        save_tex = save,
        save_html = save,
        xecjk=xecjk,
    )
