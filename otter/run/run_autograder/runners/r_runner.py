""""""

import json
import jupytext
import nbformat
import os
import pickle
import shutil

from glob import glob
from rpy2.robjects import r

from ..constants import DEFAULT_OPTIONS
from ..utils import get_source, OtterRuntimeError
from ....test_files import GradingResults
from ....utils import chdir


NBFORMAT_VERSION = 4


# TODO: push seeding down into ottr
class RRunner(AbstractLanguageRunner):

    def resolve_submission_path(self):
        # convert IPYNB files to Rmd files
        nbs = glob("*.ipynb")
        if len(nbs) > 1:
            raise OtterRuntimeError("More than one IPYNB file found in submission")

        elif len(nbs) == 1:
            nb_path = nbs[0]
            nb = jupytext.read(nb_path)
            jupytext.write(nb, os.path.splitext(nb_path)[0] + ".Rmd")

        # convert Rmd files to R files
        rmds = glob("*.Rmd")
        if len(rmds) > 1:
            raise OtterRuntimeError("More than one Rmd file found in submission")

        elif len(rmds) == 1:
            rmd_path = rmds[0]
            rmd_path, script_path = \
                os.path.abspath(rmd_path), os.path.abspath(os.path.splitext(rmd_path)[0] + ".r")
            r(f"knitr::purl('{rmd_path}', '{script_path}')")

        # get the R script
        scripts = glob("*.[Rr]")
        if len(scripts) > 1:
            raise OtterRuntimeError("More than one R script found in submission")

        elif len(scripts) == 0:
            raise OtterRuntimeError("No gradable files found in submission")

        return scripts[0]

    # TODO
    def write_pdf(self, subm_path):
        """
        Generate a PDF of a notebook at ``subm_path`` using the options in ``self.options`` and 
        return the that to the PDF.
        """
        try:
            pdf_path = os.path.splitext(subm_path)[0] + ".pdf"
            export_notebook(
                subm_path, dest=pdf_path, filtering=self.options["filtering"], 
                pagebreaks=self.options["pagebreaks"], exporter_type="latex")

        except Exception as e:
            print(f"\n\nError encountered while generating and submitting PDF:\n{e}")

        return pdf_path

    # TODO
    def submit_pdf(self, client, pdf_path):
        """
        Upload a PDF to a Gradescope assignment for manual grading.

        Args:
            client (``otter.generate.token.APIClient``): the Gradescope client
            pdf_path (``str``): path to the PDF
        """
        try:
            # get student email
            with open("../submission_metadata.json") as f:
                metadata = json.load(f)

            student_emails = []
            for user in metadata["users"]:
                student_emails.append(user["email"])

            for student_email in student_emails:
                client.upload_pdf_submission(
                    self.options["course_id"], self.options["assignment_id"], student_email, pdf_path)

            print("\n\nSuccessfully uploaded submissions for: {}".format(", ".join(student_emails)))

        except Exception as e:
            print(f"\n\nError encountered while generating and submitting PDF:\n{e}")

    def run(self):
        os.environ["PATH"] = f"{self.options['miniconda_path']}/bin:" + os.environ.get("PATH")

        with chdir("./submission"):
            subm_path = self.resolve_submission_path()
            output = r(f"""ottr::run_autograder("{subm_path}")""")[0]
            scores = GradingResults.from_ottr_json(output)

        return scores
