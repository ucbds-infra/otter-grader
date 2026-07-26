"""Autograder runner for R assignments"""

import copy
import frontmatter
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
from ....test_files import GradingResults
from ....utils import chdir, get_source, knit_rmd_file, NBFORMAT_VERSION, qmd_to_pdf


_OTTR = importr("ottr")


class RRunner(AbstractLanguageRunner):

    subm_path_deletion_required = False
    """whether the submission path needs to be deleted (because it was created with tempfile)"""

    def validate_submission(self, submission_path: str):
        assignment_name = False
        ext = os.path.splitext(submission_path)[1].lower()
        if ext == ".ipynb":
            nb = nbf.read(submission_path, as_version=nbf.NO_CONVERT)
            assignment_name = self.get_notebook_assignment_name(nb)

        elif ext == ".rmd" or ext == ".qmd":
            post = frontmatter.load(submission_path)
            assignment_name = post.get("assignment_name", None)

        else:
            raise ValueError(f"Unexpected submission path extension: {ext}")

        if assignment_name is not False:
            self.validate_assignment_name(assignment_name)

    def filter_cells_with_syntax_errors(self, nb: nbf.NotebookNode) -> nbf.NotebookNode:
        """
        Filter out cells in an R notebook with syntax errors.
        """
        new_cells = []
        for cell in nb["cells"]:
            if cell["cell_type"] == "code":
                source = "\n".join(get_source(cell))
                valid_syntax = _OTTR.valid_syntax(source)[0]
                if valid_syntax:
                    new_cells.append(cell)
        nb = copy.deepcopy(nb)
        nb["cells"] = new_cells
        return nb

    def add_seeds_to_rmd_file(self, rmd_path: str):
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
            # Put the seed on the first non-comment line; this prevents the seed from being inserted
            # before Quarto cell metadata, which prevents it from being respected. (Esp. important
            # for cells with "eval: false".)
            while i + 1 < len(lines) and lines[i + 1].startswith("#"):
                i += 1
            lines.insert(i + 1, seed)

        with open(rmd_path, "w") as f:
            f.write("\n".join(lines))

    def add_seed_to_script(self, script_path: str):
        """
        Add a line calling ``set.seed`` to the top of the R script at the specified path.
        """
        with open(script_path) as f:
            script = f.read()

        script = f"set.seed({self.ag_config.seed})\n" + script

        with open(script_path, "w") as f:
            f.write(script)

    def resolve_submission_path(self) -> str:
        # create a temporary file at which to write a script if necessary
        script_fd, script_path = tempfile.mkstemp(suffix=".R")

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

        # convert Rmd/qmd files to R scripts
        rmds = glob("*.[Rq]md")
        if len(rmds) > 1:
            raise OtterRuntimeError("More than one Rmd or qmd file found in submission")

        elif len(rmds) == 1:
            rmd_path = rmds[0]

            self.validate_submission(rmd_path)

            # add seeds
            if self.ag_config.seed is not None:
                self.add_seeds_to_rmd_file(rmd_path)

            # create the R script
            rmd_path = os.path.abspath(rmd_path)
            if os.path.splitext(rmd_path)[1] == ".Rmd":
                importr("knitr").purl(rmd_path, script_path)
            else:
                # delete the script tempfile since quarto::qmd_to_r_script requires no file to exist
                # at the output path
                os.close(script_fd)
                os.remove(script_path)
                # use quarto::qmd_to_r_script for the conversion because it will ensure that cells
                # marked with "eval: false" are commented out in the resulting script (precenting a
                # fork bomb caused by ottr::export)
                importr("quarto").qmd_to_r_script(rmd_path, script=script_path)

            self.subm_path_deletion_required = True
            return script_path

        os.close(script_fd)
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

    def write_pdf(self, submission_path: str) -> str:
        # NOTE: this method ignores the submission_path argument, and instead resolves it again
        # manually
        nbs = glob("*.ipynb")
        if nbs:
            subm_path = nbs[0]
            ipynb = True

        else:
            rmds = glob("*.[Rq]md")
            if rmds:
                subm_path = rmds[0]
                ipynb = False

            else:
                raise OtterRuntimeError("Could not find a file that can be converted to a PDF")

        pdf_path = os.path.splitext(subm_path)[0] + ".pdf"
        if ipynb:
            export_notebook(
                subm_path,
                dest=pdf_path,
                filtering=self.ag_config.filtering,
                pagebreaks=self.ag_config.pagebreaks,
                exporter_type="html" if self.ag_config.pdf_via_html else "latex",
            )

        elif os.path.splitext(subm_path)[1] == ".qmd":
            qmd_to_pdf(subm_path, pdf_path)

        else:
            knit_rmd_file(subm_path, pdf_path)

        return pdf_path

    def _check_ottr_version(self):
        if glob("*.qmd"):
            # Require ottr>=1.6.0 for qmd submissions
            version = importr("utils").packageVersion("ottr")[0]
            if version[0] <= 1 and version[1] < 6:
                raise ValueError(
                    f"Grading qmd files requires ottr>=1.6.0 but found version {'.'.join(str(i) for i in version)}"
                )

    def run(self):
        os.environ["PATH"] = f"{self.ag_config.miniconda_path}/bin:" + os.environ.get("PATH", "")

        with chdir("./submission"):
            self._check_ottr_version()

            pdf_error = None
            if self.pdf_enabled:
                pdf_error = self.write_and_maybe_submit_pdf(None)

            self.sanitize_tokens()

            subm_path = self.resolve_submission_path()
            output = _OTTR.run_autograder(
                subm_path, ignore_errors=not self.ag_config.debug, test_dir="./tests"
            )[0]
            scores = GradingResults.from_ottr_json(output)

            if pdf_error:
                scores.set_pdf_error(pdf_error)

        # delete the script if necessary
        if self.subm_path_deletion_required:
            os.remove(subm_path)
            self.subm_path_deletion_required = False

        return scores
