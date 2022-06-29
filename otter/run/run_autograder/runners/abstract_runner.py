"""Abstract runner class for the autograder"""

import os
import shutil
import warnings

from abc import ABC, abstractmethod

from otter.run.run_autograder.utils import OtterRuntimeError

from ..constants import DEFAULT_OPTIONS

from ....test_files import NOTEBOOK_METADATA_KEY


class AbstractLanguageRunner(ABC):
    """
    A class defining the logic of running the autograder and generating grading results.

    Args:
        otter_config (``dict[str:object]``): user-specified configurations to override the defaults
        **kwargs: other user-specified configurations to override the defaults

    Attributes:
        options (``dict[str:object]``): the grading options, including default values from 
            ``otter.run.run_autograder.constants.DEFAULT_OPTIONS``
    """

    def __init__(self, otter_config, **kwargs):
        self.options = DEFAULT_OPTIONS.copy()
        self.options.update(otter_config)
        self.options.update(kwargs)

    @staticmethod
    def determine_language(otter_config, **kwargs):
        """
        Determine the language of the assignment based on user-specified configurations.
        """
        return kwargs.get("lang", otter_config.get("lang", DEFAULT_OPTIONS["lang"]))

    def get_option(self, option):
        """
        Return the value of a configuration, including defaults.
        """
        return self.options[option]

    def get_options(self):
        """
        Return the options dictionary, including defaults.
        """
        return self.options

    def prepare_files(self):
        """
        Copies tests and support files needed for running the autograder.

        When this method is invoked, the working directory is assumed to already be 
        ``self.options["autograder_dir"]``.
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

    def abort_or_warn_if_invalid_uuid(self, got):
        """
        Raise an ``OtterRuntimeError`` or a ``UserWarning`` (depending on configuration) if the
        UUID of the notebook is invalid.

        If no assignment UUID was provided in the configurations, no action is taken.

        Args:
            got (``str | None``): the UUID of the submission or ``None`` if it didn't have one

        Raises:
            ``otter.runb.run_autograder.utils.OtterRuntimeError``: if the UUID is invalid and
                grading should be aborted
        """
        if self.options["assignment_uuid"] and got != self.options["assignment_uuid"]:
            message = f"Received submission with UUID '{got}' (expected '{self.options['assignment_uuid']}')"
            if self.options["allow_different_uuid"]:
                warnings.warn(message)
            else:
                raise OtterRuntimeError(message)

    def get_notebook_uuid(self, nb):
        """
        Get the assignment UUID in the metadata of the provided notebook, if any.

        Args:
            nb (``nbformat.NotebookNode``): the notebook

        Returns:
            ``str | None``: the assignment UUID of the notebook, if any
        """
        if NOTEBOOK_METADATA_KEY not in nb["metadata"]:
            return None

        return nb["metadata"][NOTEBOOK_METADATA_KEY].get("assignment_uuid", None)

    @abstractmethod
    def validate_uuid(self, submission_path):
        """
        Validate the UUID of the submission, raising an error/warning if appropriate.

        This method should be invoked as part of the implementation of another abstract method
        (either ``resolve_submission_path`` or ``run``).

        Args:
            submission_path (``str``): the path to the submission file

        Raises:
            ``otter.runb.run_autograder.utils.OtterRuntimeError``: if the UUID is invalid and
                grading should be aborted
        """
        ...

    @abstractmethod
    def resolve_submission_path(self):
        """
        Determine the path to the submission file, performing any necessary transformations on the
        file.

        When this method is invoked, the working directory is assumed to already be 
        ``{self.options["autograder_dir"]}/submission``.
        """
        ...

    @abstractmethod
    def run(self):
        """
        Run the autograder according to the configurations in ``self.options``.

        When this method is invoked, the working directory is assumed to already be 
        ``self.options["autograder_dir"]``.

        Returns:
            ``otter.test_files.GradingResults``: the results from grading the submission
        """
        ...
