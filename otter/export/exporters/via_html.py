"""PDF via HTML exporter"""

import os

from typing import Any

from .base_exporter import BaseExporter, TEMPLATE_DIR


# nbconvert can't be used on jupyterlite, so try importing it and raise an error if it's not found
# when the exporter is used
_NBCONVERT_ERROR = None
try:
    import nbconvert
except ImportError as e:
    nbconvert = None
    _NBCONVERT_ERROR = e


class PDFViaHTMLExporter(BaseExporter):
    """
    An exporter that uses nbconvert's WebPDF exporter to convert notebooks to PDFs via HTML.

    Attributes:
        default_options (``dict``): the default options for this exporter
    """

    default_options = BaseExporter.default_options.copy()
    default_options.update({"save_html": False, "template": "via_html"})

    @classmethod
    def convert_notebook(cls, nb_path: str, dest: str, **kwargs: Any):
        if nbconvert is None:
            raise _NBCONVERT_ERROR

        options = cls.default_options.copy()
        options.update(kwargs)

        nb = cls.load_notebook(
            nb_path, filtering=options["filtering"], pagebreaks=options["pagebreaks"]
        )

        nbconvert.TemplateExporter.extra_template_basedirs = [str(TEMPLATE_DIR)]
        orig_template_name = nbconvert.TemplateExporter.template_name
        nbconvert.TemplateExporter.template_name = options["template"]

        exporter = nbconvert.WebPDFExporter()

        try:
            pdf, _ = nbconvert.export(exporter, nb)
        except RuntimeError as e:
            # Replace nbconvert's error about installing chromium since their flag can't be passed
            # to Otter.
            if "--allow-chromium-download" in str(e):
                raise RuntimeError(
                    "No suitable version of chromium was found; please install chromium by running "
                    "'playwright install chromium'"
                )
            raise e

        pdf_path = os.path.splitext(dest)[0] + ".pdf"
        with open(pdf_path, "wb+") as f:
            f.write(pdf)

        nbconvert.TemplateExporter.template_name = orig_template_name
