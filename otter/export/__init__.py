"""IPython notebook PDF Exporter forked from nb2pdf and gsExport"""

import nbformat
import nbconvert
import os
import pkg_resources
import warnings

from .exporters import get_exporter


def export_notebook(nb_path, dest=None, debug=False, exporter_type=None, **kwargs):
    """
    Exports a notebook file at ``nb_path`` to a PDF with optional filtering and pagebreaks. Accepts
    other ``kwargs`` passed to the exporter class's ``convert_notebook`` class method.

    Args:
        nb_path (``str``): path to notebook
        dest (``str``, optional): path to write PDF
        debug (``bool``, optional): whether to run export in debug mode
        exporter_type (``str``, optional): the type of exporter to use; one of ``['html', 'latex']``
        **kwargs: additional configurations passed to exporter
    """
    # notebook = load_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)

    if dest is not None:
        pdf_name = dest
    else:
        pdf_name = os.path.splitext(nb_path)[0] + ".pdf"
        
    # notebook_to_pdf(notebook, pdf_name, save_tex=save_tex, debug=debug)
    Exporter = get_exporter(exporter_type=exporter_type)
    Exporter.convert_notebook(nb_path, pdf_name, debug=debug, **kwargs)


def main(src, *, dest=None, exporter=None, filtering=False, pagebreaks=False, save=False, debug=False):
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
        debug (``bool``): whether to run in debug mode (print full error messages)
        **kwargs: ignored kwargs (a remnant of how the argument parser is built)
    """
    export_notebook(
        src,
        dest = dest,
        exporter_type = exporter,
        filtering = filtering,
        pagebreaks = pagebreaks,
        save_tex = save,
        save_html = save,
        debug = debug
    )
