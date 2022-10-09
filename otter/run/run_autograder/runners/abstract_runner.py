"""Abstract runner class for the autograder"""

import json
import os
import shutil

from abc import ABC, abstractmethod

from ..autograder_config import AutograderConfig
from ..utils import OtterRuntimeError

from ....utils import NOTEBOOK_METADATA_KEY


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

    def __init__(self, otter_config, **kwargs):
        self.ag_config = AutograderConfig({**otter_config, **kwargs})

    @staticmethod
    def determine_language(otter_config, **kwargs):
        """
        Determine the language of the assignment based on user-specified configurations.
        """
        # TODO: use fica.Key.get_default when available
        return kwargs.get("lang", otter_config.get("lang", AutograderConfig.lang.get_value()))

    def get_option(self, option):
        """
        Return the value of a configuration, including defaults.
        """
        return self.ag_config[option]

    def get_config(self):
        """
        Return the autograder config.
        """
        return self.ag_config

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

    def validate_assignment_name(self, got):
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
            message = f"Received submission for assignment '{got}' (this is assignment " \
                f"'{self.ag_config.assignment_name}')"
            raise OtterRuntimeError(message)

    def get_notebook_assignment_name(self, nb):
        """
        Get the assignment name in the metadata of the provided notebook, if any.

        Args:
            nb (``nbformat.NotebookNode``): the notebook

        Returns:
            ``str | None``: the assignment name of the notebook, if any
        """
        if NOTEBOOK_METADATA_KEY not in nb["metadata"]:
            return None

        return nb["metadata"][NOTEBOOK_METADATA_KEY].get("assignment_name", None)

    def write_and_maybe_submit_pdf(self, client, submission_path, submit, scores):
        """
        Upload a PDF to a Gradescope assignment for manual grading.

        This method calls ``self.write_pdf`` to generate the PDF before submitting it, and catches
        any errors thrown in that function.

        This method should be called, if appropriate, by ``self.run``.

        Args:
            client (``otter.generate.token.APIClient``): the Gradescope client
            submission_path (``str``): path to the submission
            submit (``bool``): whether to submit the PDF with ``client``
            scores (``otter.test_files.GradingResults``): the grading results (so an error can be
                appended if needed)
        """
        try:
            pdf_path = self.write_pdf(submission_path)

            if submit:
                # get student email
                with open("../submission_metadata.json", encoding="utf-8") as f:
                    metadata = json.load(f)

                student_emails = []
                for user in metadata["users"]:
                    student_emails.append(user["email"])

                for student_email in student_emails:
                    client.upload_pdf_submission(
                        self.ag_config.course_id,
                        self.ag_config.assignment_id,
                        student_email,
                        pdf_path,
                    )

                print("\n\nSuccessfully uploaded submissions for: {}".format(
                    ", ".join(student_emails)))

        except Exception as e:
            print(f"\n\nError encountered while generating and submitting PDF:\n{e}")
            scores.set_pdf_error(e)

    @abstractmethod
    def validate_submission(self, submission_path):
        """
        Validate the submission, raising an error/warning if appropriate.

        This method should be invoked as part of the implementation of another abstract method
        (either ``resolve_submission_path`` or ``run``).

        Args:
            submission_path (``str``): the path to the submission file
        """
        ...

    @abstractmethod
    def resolve_submission_path(self):
        """
        Determine the path to the submission file, performing any necessary transformations on the
        file.

        When this method is invoked, the working directory is assumed to already be 
        ``{self.ag_config.autograder_dir}/submission``.
        """
        ...

    @abstractmethod
    def write_pdf(self, submission_path):
        """
        Convert the submission to a PDF, returning the path to the PDF file.

        Args:
            submission_path (``str``): the path to the submission

        Returns:
            ``str``: the path to the generated PDF
        """
        ...

    @abstractmethod
    def run(self):
        """
        Run the autograder according to the configurations in ``self.ag_config``.

        When this method is invoked, the working directory is assumed to already be 
        ``self.ag_config.autograder_dir``.

        Returns:
            ``otter.test_files.GradingResults``: the results from grading the submission
        """
        ...
