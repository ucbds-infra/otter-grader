"""
IPython notebook PDF Exporter forked from nb2pdf and gsExport
"""

import os
import warnings
import nbformat
import nbconvert
import pkg_resources

from .exporters import get_exporter

# def notebook_to_pdf(nb, dest, templating="test.tplx", save_tex=False, debug=False):
#     """
#     Writes a parsed notebook ``nb`` to a PDF file using nbconvert. Forked from
#     https://github.com/dibyaghosh/gsExport/blob/master/gsExport/utils.py
    
#     Args:
#         nb (``nbformat.NotebookNode``): parsed notebook
#         dest (``str``): path to write PDF
#         templating (``str``, optional): path to template file relative to install directory of Otter
#         save_tex (``bool``, optional): whether to save the LaTeX file as well
#         debug (``bool``, optional): whether to run export in debug mode
#     """
#     warnings.filterwarnings("ignore", r"invalid escape sequence '\\c'", DeprecationWarning)

#     if save_tex:
#         latex_exporter = nbconvert.LatexExporter()

#     pdf_exporter = nbconvert.PDFExporter()
#     pdf_exporter.template_file = pkg_resources.resource_filename(__name__, templating)
#     try:
#         pdf_output = pdf_exporter.from_notebook_node(nb)
#         with open(dest, "wb") as output_file:
#             output_file.write(pdf_output[0])
#         if save_tex:
#             latex_output = latex_exporter.from_notebook_node(nb)
#             with open(os.path.splitext(dest)[0] + ".tex", "w+") as output_file:
#                 output_file.write(latex_output[0])
#     except nbconvert.pdf.LatexFailed as error:
#         print("There was an error generating your LaTeX")
#         output = error.output
#         if debug:
#             print("Showing full error message from PDFTex")

#         else:
#             print("Showing concise error message")
#             output = "\n".join(error.output.split("\n")[-15:])
#         print("=" * 60)
#         print(output)
#         print("=" * 60)

def export_notebook(nb_path, dest=None, debug=False, exporter_type=None, **kwargs):
    """
    Exports a notebook file at ``nb_path`` to a PDF with optional filtering and pagebreaks

    Args:
        nb_path (``str``): path to notebook
        dest (``str``, optional): path to write PDF
        debug (``bool``, optional): whether to run export in debug mode
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
