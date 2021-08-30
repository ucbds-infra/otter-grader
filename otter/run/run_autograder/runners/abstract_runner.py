"""Abstract runner class for the autograder"""

import os
import shutil

from abc import ABC, abstractmethod

from ..constants import DEFAULT_OPTIONS


class AbstractLanguageRunner(ABC):
    """
    A class defining the logic of running the autograder and generating grading results.

    Args:
        otter_config (``dict[str:object]``): user-specified configurations to override the defaults
        **kwargs: other user-specified confirations to override the defaults

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

        Retuns:
            ``otter.test_files.GradingResults``: the results from grading the submission
        """
        ...
