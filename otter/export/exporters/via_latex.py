"""PDF via LaTeX exporter"""

import os
import warnings

from textwrap import indent
from typing import Any

from .base_exporter import BaseExporter, ExportFailedException, TEMPLATE_DIR


# nbconvert can't be used on jupyterlite, so try importing it and raise an error if it's not found
# when the exporter is used
_NBCONVERT_ERROR = None
try:
    import nbconvert
except ImportError as e:
    nbconvert = None
    _NBCONVERT_ERROR = e


class PDFViaLatexExporter(BaseExporter):
    """
    An exporter that uses nbconvert's PDF exporter to convert notebooks to PDFs via LaTeX.

    Attributes:
        default_options (``dict``): the default options for this exporter
    """

    default_options = BaseExporter.default_options.copy()
    default_options.update(
        {
            "save_tex": False,
            "template": "via_latex",
        }
    )

    @classmethod
    def convert_notebook(cls, nb_path: str, dest: str, *, xecjk: bool = False, **kwargs: Any):
        if nbconvert is None:
            raise _NBCONVERT_ERROR

        warnings.filterwarnings("ignore", r"invalid escape sequence '\\c'", DeprecationWarning)

        options = cls.default_options.copy()
        options.update(kwargs)

        # choose the template to allow Chinese, Japanese, and Korean characters if necessary
        if xecjk:
            options["template"] = "via_latex_xecjk"

        nb = cls.load_notebook(
            nb_path, filtering=options["filtering"], pagebreaks=options["pagebreaks"]
        )

        nbconvert.TemplateExporter.extra_template_basedirs = [str(TEMPLATE_DIR)]
        orig_template_name = nbconvert.TemplateExporter.template_name
        nbconvert.TemplateExporter.template_name = options["template"]

        if options["save_tex"]:
            latex_exporter = nbconvert.LatexExporter()

        pdf_exporter = nbconvert.PDFExporter()

        try:
            if options["save_tex"]:
                latex_output = nbconvert.export(latex_exporter, nb)
                with open(os.path.splitext(dest)[0] + ".tex", "w+") as output_file:
                    output_file.write(latex_output[0])

            pdf_output = nbconvert.export(pdf_exporter, nb)
            with open(dest, "wb") as output_file:
                output_file.write(pdf_output[0])

        except nbconvert.exporters.pdf.LatexFailed as error:
            message = "There was an error generating your LaTeX; showing full error message:\n"
            message += indent(error.output, "    ")
            if xecjk:
                message += (
                    "\n\nIf the error above is related to xeCJK or fandol in LaTeX "
                    "and you don't require this functionality, try running again without "
                    "xecjk set to True or the --xecjk flag."
                )
            raise ExportFailedException(message)

        finally:
            nbconvert.TemplateExporter.template_name = orig_template_name
