"""PDF via HTML exporter"""

import nbconvert
import os
import shutil

from .base_exporter import BaseExporter, TEMPLATE_DIR


class PDFViaHTMLExporter(BaseExporter):
    """
    Exports notebooks to PDF files using HTML as an intermediary

    Converts IPython notebooks to PDFs by first converting them into temporary HTML files that are then
    converted to PDFs using wkhtmltopdf and its Python API pdfkit which are then stitched together (if
    pagebreaks are enabled) using pypdf.

    Attributes:
        default_options (``dict``): the default options for this exporter
    """

    default_options = BaseExporter.default_options.copy()
    default_options.update({
        "save_html": False,
        "template": "via_html"
    })

    @classmethod
    def convert_notebook(cls, nb_path, dest, **kwargs):
        if shutil.which("wkhtmltopdf") is None:
            raise RuntimeError("Cannot export via HTML without wkhtmltopdf")

        options = cls.default_options.copy()
        options.update(kwargs)

        nb = cls.load_notebook(nb_path, filtering=options["filtering"], pagebreaks=options["pagebreaks"])

        nbconvert.TemplateExporter.extra_template_basedirs = [TEMPLATE_DIR]
        orig_template_name = nbconvert.TemplateExporter.template_name
        nbconvert.TemplateExporter.template_name = options["template"]

        exporter = nbconvert.WebPDFExporter()

        pdf, _ = nbconvert.export(exporter, nb)
        pdf_path = os.path.splitext(dest)[0] + ".pdf"
        with open(pdf_path, "wb+") as f:
            f.write(pdf)

        nbconvert.TemplateExporter.template_name = orig_template_name
