"""Autograder runner for R assignments"""

import copy
import nbformat as nbf
import os
import re
import tempfile
import yaml

from glob import glob
from nbconvert.exporters import ScriptExporter
from rpy2.robjects.packages import importr

from .abstract_runner import AbstractLanguageRunner

from ..utils import OtterRuntimeError

from ....export import export_notebook
from ....generate.token import APIClient
from ....test_files import GradingResults
from ....utils import chdir, get_source, knit_rmd_file, NBFORMAT_VERSION


R_PACKAGES = {
    "knitr": importr("knitr"),
    "ottr": importr("ottr"),
}

RMD_YAML_REGEX = r"^\n*---\n([\s\S]+?)\n---"


class RRunner(AbstractLanguageRunner):

    subm_path_deletion_required = False
    """whether the submission path needs to be deleted (because it was created with tempfile)"""

    def validate_submission(self, submission_path):
        assignment_name = False
        ext = os.path.splitext(submission_path)[1].lower()
        if ext == ".ipynb":
            nb = nbf.read(submission_path, as_version=nbf.NO_CONVERT)
            assignment_name = self.get_notebook_assignment_name(nb)

        elif ext == ".rmd":
            assignment_name = None
            with open(submission_path) as f:
                rmd = f.read()
            config = re.match(RMD_YAML_REGEX, rmd)
            if config:
                config = config.group(1)
                assignment_name = yaml.full_load(config).get("assignment_name", None)

        if assignment_name is not False:
            self.validate_assignment_name(assignment_name)

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

        seed = f"set.seed({self.ag_config.seed})"
        if self.ag_config.seed_variable:
            seed = f"{self.ag_config.seed_variable} = {self.ag_config.seed}"

        for i in insertions[::-1]:
            lines.insert(i + 1, seed)

        with open(rmd_path, "w") as f:
            f.write("\n".join(lines))

    def add_seed_to_script(self, script_path):
        """
        Add a line calling ``set.seed`` to the top of the R script at the specified path.
        """
        with open(script_path) as f:
            script = f.read()

        script = f"set.seed({self.ag_config.seed})\n" + script

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
            self.validate_submission(nb_path)
            nb = nbf.read(nb_path, as_version=NBFORMAT_VERSION)
            nb = self.filter_cells_with_syntax_errors(nb)

            # create the R script
            script, _ = ScriptExporter().from_notebook_node(nb)
            with open(script_path, "w") as f:
                f.write(script)

            self.subm_path_deletion_required = True
            return script_path

        # convert Rmd files to R files
        rmds = glob("*.Rmd")
        if len(rmds) > 1:
            raise OtterRuntimeError("More than one Rmd file found in submission")

        elif len(rmds) == 1:
            rmd_path = rmds[0]

            self.validate_submission(rmd_path)

            # add seeds
            if self.ag_config.seed is not None:
                self.add_seeds_to_rmd_file(rmd_path)

            # create the R script
            rmd_path = os.path.abspath(rmd_path)
            R_PACKAGES["knitr"].purl(rmd_path, script_path)

            self.subm_path_deletion_required = True
            return script_path

        os.remove(script_path)

        # get the R script
        scripts = glob("*.[Rr]")
        if len(scripts) > 1:
            raise OtterRuntimeError("More than one R script found in submission")

        elif len(scripts) == 0:
            raise OtterRuntimeError("No gradable files found in submission")

        if self.ag_config.seed is not None:
            self.add_seed_to_script(scripts[0]) 

        return scripts[0]

    def write_pdf(self, _):
        # NOTE: this method ignores the submission_path argument, and instead resolves it again
        # manually
        # TODO: de-deduplicate this path resolution logic with resolve_submission_path
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
                subm_path, dest=pdf_path, filtering=self.ag_config.filtering, 
                pagebreaks=self.ag_config.pagebreaks, exporter_type="latex")

        else:
            knit_rmd_file(subm_path, pdf_path)

        return pdf_path

    def run(self):
        os.environ["PATH"] = f"{self.ag_config.miniconda_path}/bin:" + os.environ.get("PATH")

        with chdir("./submission"):
            if self.ag_config.token is not None:
                client = APIClient(token=self.ag_config.token)
                generate_pdf = True
                has_token = True

            else:
                generate_pdf = self.ag_config.pdf
                has_token = False
                client = None

            subm_path = self.resolve_submission_path()
            output = R_PACKAGES["ottr"].run_autograder(
                subm_path, ignore_errors = not self.ag_config.debug)[0]
            scores = GradingResults.from_ottr_json(output)

            if generate_pdf:
                self.write_and_maybe_submit_pdf(client, None, has_token, scores)

        # delete the script if necessary
        if self.subm_path_deletion_required:
            os.remove(subm_path)
            self.subm_path_deletion_required = False

        return scores
