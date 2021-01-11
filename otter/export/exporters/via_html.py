"""
PDF via HTML exporter
"""

import os
import tempfile
import shutil
import pdfkit
import nbconvert
import pkg_resources

from io import StringIO, BytesIO
from contextlib import redirect_stdout, redirect_stderr
from nbconvert.exporters import export
from PyPDF2 import PdfFileMerger

from .base_exporter import BaseExporter, NBCONVERT_6, TEMPLATE_DIR
from .utils import notebook_pdf_generator

class PDFViaHTMLExporter(BaseExporter):
    """
    Exports notebooks to PDF files using HTML as an intermediary

    Converts IPython notebooks to PDFs by first converting them into temporary HTML files that are then
    converted to PDFs using wkhtmltopdf and its Python API pdfkit which are then stitched together (if
    pagebreaks are enabled) using PyPDF2.

    Attributes:
        default_options (``dict``): the default options for this exporter
    """

    default_options = BaseExporter.default_options.copy()
    default_options.update({
        "save_html": False,
        "template": "via_html"
    })

    @classmethod
    def convert_notebook(cls, nb_path, dest, debug=False, **kwargs):
        assert shutil.which("wkhtmltopdf") is not None, "Cannot export via HTML without wkhtmltopdf"

        options = cls.default_options.copy()
        options.update(kwargs)

        nb = cls.load_notebook(nb_path, filtering=options["filtering"], pagebreaks=options["pagebreaks"])

        if NBCONVERT_6:
            nbconvert.TemplateExporter.extra_template_basedirs = [TEMPLATE_DIR]
            orig_template_name = nbconvert.TemplateExporter.template_name
            nbconvert.TemplateExporter.template_name = options["template"]

        exporter = nbconvert.HTMLExporter()
        if not NBCONVERT_6:
            exporter.template_file = os.path.join(TEMPLATE_DIR, options["template"] + ".tpl")

        if options["save_html"]:
            html, _ = export(exporter, nb)
            html_path = os.path.splitext(dest)[0] + ".html"
            with open(html_path, "wb+") as f:
                f.write(html.encode("utf-8"))
        
        merger = PdfFileMerger()
        for subnb in notebook_pdf_generator(nb):
            html, _ = export(exporter, subnb)

            pdfkit_options = {
                'enable-local-file-access': None, 
                'quiet': '', 
                'print-media-type': '', 
                'javascript-delay': 2000
            }
            pdf_contents = pdfkit.from_string(html, False, options=pdfkit_options)

            output = BytesIO()
            output.write(pdf_contents)
            output.seek(0)

            merger.append(output, import_bookmarks=False)

        merger.write(dest)

        if NBCONVERT_6:
            nbconvert.TemplateExporter.template_name = orig_template_name
