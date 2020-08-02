"""
PDF via LaTeX exporter
"""

import os
import warnings
import pkg_resources
import nbconvert

from .base_exporter import BaseExporter

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
        "template": "templates/via_latex.tpl",
    })

    @classmethod
    def convert_notebook(cls, nb_path, dest, debug=False, **kwargs):
        warnings.filterwarnings("ignore", r"invalid escape sequence '\\c'", DeprecationWarning)

        options = cls.default_options.copy()
        options.update(kwargs)

        nb = cls.load_notebook(nb_path, filtering=options["filtering"], pagebreaks=options["pagebreaks"])

        if options["save_tex"]:
            latex_exporter = nbconvert.LatexExporter()
            latex_exporter.template_file = pkg_resources.resource_filename(__name__, options["template"])

        pdf_exporter = nbconvert.PDFExporter()
        pdf_exporter.template_file = pkg_resources.resource_filename(__name__, options["template"])

        try:
            pdf_output = pdf_exporter.from_notebook_node(nb)
            with open(dest, "wb") as output_file:
                output_file.write(pdf_output[0])

            if options["save_tex"]:
                latex_output = latex_exporter.from_notebook_node(nb)
                with open(os.path.splitext(dest)[0] + ".tex", "w+") as output_file:
                    output_file.write(latex_output[0])

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
