"""
PDF via LaTeX exporter
"""

import os
import warnings
import pkg_resources
import nbconvert

from .base_exporter import BaseExporter, NBCONVERT_6, TEMPLATE_DIR

class PDFViaLatexExporter(BaseExporter):
    """
    Exports notebooks to PDF files using LaTeX as an intermediary

    Converts IPython notebooks to PDFs by first converting them into temporary TeX files that are then
    converted to PDFs using nbconvert and pandoc. Pagebreaks, if enabled, are enforced with a custom
    LaTeX template that clears the document to the next odd numbered page, resulting in responses that
    are all two pages long.

    Attributes:
        default_options (``dict``): the default options for this exporter
    """

    default_options = BaseExporter.default_options.copy()
    default_options.update({
        "save_tex": False,
        "template": "via_latex",
    })

    @classmethod
    def convert_notebook(cls, nb_path, dest, debug=False, **kwargs):
        warnings.filterwarnings("ignore", r"invalid escape sequence '\\c'", DeprecationWarning)

        options = cls.default_options.copy()
        options.update(kwargs)

        nb = cls.load_notebook(nb_path, filtering=options["filtering"], pagebreaks=options["pagebreaks"])

        if NBCONVERT_6:
            nbconvert.TemplateExporter.extra_template_basedirs = [TEMPLATE_DIR]
            orig_template_name = nbconvert.TemplateExporter.template_name
            nbconvert.TemplateExporter.template_name = options["template"]

        if options["save_tex"]:
            latex_exporter = nbconvert.LatexExporter()
            if not NBCONVERT_6:
                latex_exporter.template_file = os.path.join(TEMPLATE_DIR, options["template"] + ".tpl")

        pdf_exporter = nbconvert.PDFExporter()
        if not NBCONVERT_6:
            pdf_exporter.template_file = os.path.join(TEMPLATE_DIR, options["template"] + ".tpl")

        try:
            pdf_output = pdf_exporter.from_notebook_node(nb)
            with open(dest, "wb") as output_file:
                output_file.write(pdf_output[0])

            if options["save_tex"]:
                latex_output = latex_exporter.from_notebook_node(nb)
                with open(os.path.splitext(dest)[0] + ".tex", "w+") as output_file:
                    output_file.write(latex_output[0])

            if NBCONVERT_6:
                nbconvert.TemplateExporter.template_name = orig_template_name

        except nbconvert.pdf.LatexFailed as error:
            print("There was an error generating your LaTeX")
            output = error.output
            if debug:
                print("Showing full error message from PDFTex")

            else:
                print("Showing concise error message")
                output = "\n".join(error.output.split("\n")[-15:])

            print("=" * 60)
            print(output)
            print("=" * 60)

            if NBCONVERT_6:
                nbconvert.TemplateExporter.template_name = orig_template_name
