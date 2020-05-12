import os
import nbformat
import nbconvert
import pkg_resources

from .filter import load_notebook


def notebook_to_pdf(nb, dest=None, templating="test.tplx", debug=False):
    """
    https://github.com/dibyaghosh/gsExport/blob/master/gsExport/utils.py
    """
    pdf_exporter = nbconvert.PDFExporter()
    pdf_exporter.template_file = pkg_resources.resource_filename(__name__, templating)
    try:
        pdf_output = pdf_exporter.from_notebook_node(nb)
        with open(dest, "wb") as output_file:
            output_file.write(pdf_output[0])
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
        # return None
    # return "%s.pdf" % name


def export_notebook(nb_path, dest=None, filtering=True, pagebreaks=False, debug=False):
    notebook = load_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)

    if dest is not None:
        pdf_name = dest
    else:
        pdf_name = os.path.splitext(nb_path)[0] + ".pdf"
        
    notebook_to_pdf(notebook, pdf_name, debug=debug)


def main(args):
    export_notebook(
        args.source,
        dest = args.dest,
        filtering = args.filtering,
        pagebreaks = args.pagebreaks,
        debug = args.debug
    )
