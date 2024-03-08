"""PDF via HTML exporter"""

import nbconvert
import os

from .base_exporter import BaseExporter, TEMPLATE_DIR


class PDFViaHTMLExporter(BaseExporter):
    """
    An exporter that uses nbconvert's WebPDF exporter to convert notebooks to PDFs via HTML.

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
