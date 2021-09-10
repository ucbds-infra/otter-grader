"""Autograder runner for R assignments"""

import copy
import json
import nbformat
import os
import pickle
import shutil
import tempfile

from glob import glob
from nbconvert.exporters import ScriptExporter
from rpy2.robjects.packages import importr

from .abstract_runner import AbstractLanguageRunner
from ..utils import OtterRuntimeError
from ....export import export_notebook
from ....generate.token import APIClient
from ....test_files import GradingResults
from ....utils import chdir, get_source, knit_rmd_file


NBFORMAT_VERSION = 4
R_PACKAGES = {
    "knitr": importr("knitr"),
    "ottr": importr("ottr"),
}


class RRunner(AbstractLanguageRunner):

    subm_path_deletion_reauired = False
    """whether the submission path needs to be deleted (because it was created with tempfile)"""

    def filter_cells_with_syntax_errors(self, nb):
        """
        Filter out cells in an R notebook with syntax errors.
        """
        new_cells = []
        for cell in nb["cells"]:
            if cell["cell_type"] == "code":
                source = "\n".join(get_source(cell))
                valid_syntax = R_PACKAGES["ottr"].valid_syntax(source)[0]
                if valid_syntax:
                    new_cells.append(cell)
        nb = copy.deepcopy(nb)
        nb["cells"] = new_cells
        return nb

    def add_seeds_to_rmd_file(self, rmd_path):
        """
        Add intercell seeding to an Rmd file.
        """
        with open(rmd_path) as f:
            rmd = f.read()

        lines = rmd.split("\n")
        insertions = []
        for i, line in enumerate(lines):
            if line.startswith("```{r"):
                insertions.append(i)

        seed = f"set.seed({self.options['seed']})"
        if self.options["seed_variable"]:
            seed = f"{self.options['seed_variable']} = {self.options['seed']}"

        for i in insertions[::-1]:
            lines.insert(i + 1, seed)

        with open(rmd_path, "w") as f:
            f.write("\n".join(lines))

    def add_seed_to_script(self, script_path):
        """
        Add intercell seeding to an Rmd file.
        """
        with open(script_path) as f:
            script = f.read()

        script = f"set.seed({self.options['seed']})\n" + script

        with open(script_path, "w") as f:
            f.write(script)

    def resolve_submission_path(self):
        # create a temporary file at which to write a script if necessary
        _, script_path = tempfile.mkstemp(suffix=".R")

        # convert IPYNB files to Rmd files
        nbs = glob("*.ipynb")
        if len(nbs) > 1:
            raise OtterRuntimeError("More than one IPYNB file found in submission")

        elif len(nbs) == 1:
            nb_path = nbs[0]
            nb = nbformat.read(nb_path, as_version=NBFORMAT_VERSION)
            nb = self.filter_cells_with_syntax_errors(nb)

            # create the R script
            script, _ = ScriptExporter().from_notebook_node(nb)
            with open(script_path, "w") as f:
                f.write(script)

            self.subm_path_deletion_reauired = True
            return script_path

        # convert Rmd files to R files
        rmds = glob("*.Rmd")
        if len(rmds) > 1:
            raise OtterRuntimeError("More than one Rmd file found in submission")

        elif len(rmds) == 1:
            rmd_path = rmds[0]

            # add seeds
            if self.options["seed"] is not None:
                self.add_seeds_to_rmd_file(rmd_path)

            # create the R script
            rmd_path = os.path.abspath(rmd_path)
            R_PACKAGES["knitr"].purl(rmd_path, script_path)

            self.subm_path_deletion_reauired = True
            return script_path

        os.remove(script_path)

        # get the R script
        scripts = glob("*.[Rr]")
        if len(scripts) > 1:
            raise OtterRuntimeError("More than one R script found in submission")

        elif len(scripts) == 0:
            raise OtterRuntimeError("No gradable files found in submission")

        if self.options["seed"] is not None:
            self.add_seed_to_script(scripts[0]) 

        return scripts[0]

    def write_pdf(self):
        """
        Generate a PDF of a submission using the options in ``self.options`` and return the that to 
        the PDF.
        """
        try:
            nbs = glob("*.ipynb")
            if nbs:
                subm_path = nbs[0]
                ipynb = True

            else:
                rmds = glob("*.Rmd")
                if rmds:
                    subm_path = rmds[0]
                    ipynb = False

                else:
                    raise OtterRuntimeError("Could not find a file that can be converted to a PDF")

            pdf_path = os.path.splitext(subm_path)[0] + ".pdf"
            if ipynb:
                export_notebook(
                    subm_path, dest=pdf_path, filtering=self.options["filtering"], 
                    pagebreaks=self.options["pagebreaks"], exporter_type="latex")

            else:
                knit_rmd_file(subm_path, pdf_path)

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
            with open("../submission_metadata.json", encoding="utf-8") as f:
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
            if self.options["token"] is not None:
                client = APIClient(token=self.options["token"])
                generate_pdf = True
                has_token = True

            else:
                generate_pdf = self.options["pdf"]
                has_token = False
                client = None

            subm_path = self.resolve_submission_path()
            ignore_errors = "FALSE" if self.options["debug"] else "TRUE"
            output = R_PACKAGES["ottr"].run_autograder(
                subm_path, ignore_errors = not self.options["debug"])[0]
            scores = GradingResults.from_ottr_json(output)

            if generate_pdf:
                pdf_path = self.write_pdf()

                if has_token:
                    self.submit_pdf(client, pdf_path)

        # delete the script if necessary
        if self.subm_path_deletion_reauired:
            os.remove(subm_path)
            self.subm_path_deletion_reauired = False

        return scores
