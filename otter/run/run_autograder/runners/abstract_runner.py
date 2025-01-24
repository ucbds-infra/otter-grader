"""Abstract runner class for the autograder"""

import gc
import json
import nbformat
import os
import shutil
import tempfile

from abc import ABC, abstractmethod
from glob import glob
from typing import Optional

from ..autograder_config import AutograderConfig
from ..utils import OtterRuntimeError, print_output, write_blank_page_to_stare_at_before_you
from ....generate.token import APIClient
from ....nbmeta_config import NBMetadataConfig
from ....test_files import GradingResults


class AbstractLanguageRunner(ABC):
    """
    A class defining the logic of running the autograder and generating grading results.

    Args:
        otter_config (``dict[str, object]``): user-specified configurations to override the defaults
        **kwargs: other user-specified configurations to override the defaults and values specified
            in ``otter_config``
    """

    ag_config: AutograderConfig
    """the autograder config"""

    def __init__(self, ag_config: AutograderConfig):
        self.ag_config = ag_config

    def prepare_files(self):
        """
        Copies tests and support files needed for running the autograder.

        When this method is invoked, the working directory is assumed to already be
        ``self.ag_config.autograder_dir``.
        """
        # put files into submission directory
        if os.path.exists("./source/files"):
            for file in os.listdir("./source/files"):
                fp = os.path.join("./source/files", file)
                if os.path.isdir(fp):
                    if not os.path.exists(os.path.join("./submission", os.path.basename(fp))):
                        shutil.copytree(fp, os.path.join("./submission", os.path.basename(fp)))
                else:
                    shutil.copy(fp, "./submission")

        # copy the tests directory
        if os.path.exists("./submission/tests"):
            shutil.rmtree("./submission/tests")
        shutil.copytree("./source/tests", "./submission/tests")

    def validate_assignment_name(self, got: Optional[str]):
        """
        Raise an ``OtterRuntimeError`` if the assignment name of the notebook is invalid.

        If no assignment name was provided in the configurations, no action is taken.

        Args:
            got (``str | None``): the assignment name of the submission or ``None`` if it didn't
                have one

        Raises:
            ``otter.run.run_autograder.utils.OtterRuntimeError``: if the name is invalid and
                grading should be aborted
        """
        if self.ag_config.assignment_name and got != self.ag_config.assignment_name:
            message = (
                f"Received submission for assignment '{got}' (this is assignment "
                f"'{self.ag_config.assignment_name}')"
            )
            raise OtterRuntimeError(message)

    def get_notebook_assignment_name(self, nb: nbformat.NotebookNode) -> Optional[str]:
        """
        Get the assignment name in the metadata of the provided notebook, if any.

        Args:
            nb (``nbformat.NotebookNode``): the notebook

        Returns:
            ``str | None``: the assignment name of the notebook, if any
        """
        nbmc = NBMetadataConfig.from_notebook(nb)
        return nbmc.assignment_name

    def write_and_maybe_submit_pdf(self, submission_path: str) -> Optional[Exception]:
        """
        Upload a PDF to a Gradescope assignment for manual grading.

        This method calls ``self.write_pdf`` to generate the PDF before submitting it, and catches
        any errors thrown in that function.

        This method should be called, if appropriate, by ``self.run``.

        Args:
            submission_path (``str``): path to the submission

        Returns:
            ``Exception | None``: an error thrown while trying to write or submit the PDF, if any;
                a return value of ``None`` indicates a successful export and upload
        """
        # Don't export or submit a PDF in debug mode.
        if self.ag_config.debug:
            return None

        try:
            subm_pdfs = glob("*.pdf")
            if self.ag_config.use_submission_pdf and subm_pdfs:
                pdf_path = subm_pdfs[0]
            else:
                pdf_path = self.write_pdf(submission_path)

            if self.ag_config.token:
                client = APIClient(token=self.ag_config.token)
                self.submit_pdf(client, pdf_path)

                # ensure the client gets garbage collected so that the token can't be accessed
                # by student code
                del client
                gc.collect()

        except Exception as e:
            print_output(f"\n\nError encountered while generating and submitting PDF:\n{e}")

            if self.ag_config.submit_blank_pdf_on_export_failure and self.ag_config.token:
                print_output("\nUploading a blank PDF due to export failure")
                with tempfile.NamedTemporaryFile(suffix=".pdf") as ntf:
                    write_blank_page_to_stare_at_before_you(ntf.name)
                    self.submit_pdf(client, ntf.name)

            return e

    def submit_pdf(self, client: APIClient, pdf_path: str):
        """
        Upload the PDF at ``pdf_path`` to the Gradescope assignment specified in the config. Does
        not check whether the assignment configuration is valid.

        Args:
            client (``otter.generate.token.APIClient``): the Gradescope client
            pdf_path (``str``): path to the PDF file to upload
        """
        # get student email
        with open("../submission_metadata.json", encoding="utf-8") as f:
            metadata = json.load(f)

        student_emails = []
        for user in metadata.get("users", []):
            student_emails.append(user["email"])

        # validate that a course and assignment ID were specified
        if self.ag_config.course_id is None:
            raise OtterRuntimeError("PDF upload course ID not specified")
        if self.ag_config.assignment_id is None:
            raise OtterRuntimeError("PDF upload assignment ID not specified")

        for student_email in student_emails:
            res = client.upload_pdf_submission(
                self.ag_config.course_id,
                self.ag_config.assignment_id,
                student_email,
                pdf_path,
            )
            if res.status_code != 200:
                raise OtterRuntimeError(
                    f"Failed to upload submission for {student_email}: [status {res.status_code}] {res.text}"
                )

        print_output(
            "\n\nSuccessfully uploaded submissions for: {}".format(", ".join(student_emails))
        )

    def sanitize_tokens(self):
        """
        Sanitize any references to the PDF submission upload token to prevent unauthorized access
        when executing student code.

        This method should be invoked from inside ``{self.ag_config.autograder_dir}/submission``
        as part of ``run``.
        """
        self.ag_config.token = None
        if not os.path.exists("../source/otter_config.json"):
            return
        with open("../source/otter_config.json") as f:
            c = json.load(f)
        if "token" in c:
            del c["token"]
        with open("../source/otter_config.json", "w") as f:
            json.dump(c, f, indent=2)

    @abstractmethod
    def validate_submission(self, submission_path: str):
        """
        Validate the submission, raising an error/warning if appropriate.

        This method should be invoked as part of the implementation of another abstract method
        (either ``resolve_submission_path`` or ``run``).

        Args:
            submission_path (``str``): the path to the submission file
        """
        ...

    @abstractmethod
    def resolve_submission_path(self) -> str:
        """
        Determine the path to the submission file, performing any necessary transformations on the
        file.

        When this method is invoked, the working directory is assumed to already be
        ``{self.ag_config.autograder_dir}/submission``.
        """
        ...

    @abstractmethod
    def write_pdf(self, submission_path: str) -> str:
        """
        Convert the submission to a PDF, returning the path to the PDF file.

        Args:
            submission_path (``str``): the path to the submission

        Returns:
            ``str``: the path to the generated PDF
        """
        ...

    @abstractmethod
    def run(self) -> GradingResults:
        """
        Run the autograder according to the configurations in ``self.ag_config``.

        When this method is invoked, the working directory is assumed to already be
        ``self.ag_config.autograder_dir``.

        Returns:
            ``otter.test_files.GradingResults``: the results from grading the submission
        """
        ...
