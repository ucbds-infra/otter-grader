"""Abstract runner class for the autograder"""

import os
import shutil

from abc import ABC, abstractmethod

from ..autograder_config import AutograderConfig


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
    def run(self):
        """
        Run the autograder according to the configurations in ``self.ag_config``.

        When this method is invoked, the working directory is assumed to already be 
        ``self.ag_config.autograder_dir``.

        Returns:
            ``otter.test_files.GradingResults``: the results from grading the submission
        """
        ...
