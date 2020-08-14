"""
IPython notebook PDF Exporter forked from nb2pdf and gsExport
"""

import os
import warnings
import nbformat
import nbconvert
import pkg_resources

from .exporters import get_exporter

def export_notebook(nb_path, dest=None, debug=False, exporter_type=None, **kwargs):
    """
    Exports a notebook file at ``nb_path`` to a PDF with optional filtering and pagebreaks. Accepts
    other ``kwargs`` passed to the exporter class's ``convert_notebook`` class method.

    Args:
        nb_path (``str``): path to notebook
        dest (``str``, optional): path to write PDF
        debug (``bool``, optional): whether to run export in debug mode
        exporter_type (``str``, optional): the type of exporter to use; one of {'html', 'latex'}
    """
    # notebook = load_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)

    if dest is not None:
        pdf_name = dest
    else:
        pdf_name = os.path.splitext(nb_path)[0] + ".pdf"
        
    # notebook_to_pdf(notebook, pdf_name, save_tex=save_tex, debug=debug)
    Exporter = get_exporter(exporter_type=exporter_type)
    Exporter.convert_notebook(nb_path, pdf_name, debug=debug, **kwargs)

def main(args):
    """
    Runs Otter Export

    Args:
        args (``argparse.Namespace``): parsed command line arguments
    """
    export_notebook(
        args.source,
        dest = args.dest,
        exporter_type = args.exporter,
        filtering = args.filtering,
        pagebreaks = args.pagebreaks,
        save_tex = args.save,
        save_html = args.save,
        debug = args.debug
    )
