"""
Abstract base plugin class for Otter
"""

from abc import ABC, abstractmethod


class PluginEventNotSupportedException(Exception):
    """
    Exception to raise when an event is not supported by a plugin.
    """


class AbstractOtterPlugin(ABC):
    """
    Abstract base class for Otter plugins to inherit from. Includes the following methods:

    - ``during_assign``: run during Otter Assign after output directories are written
    - ``during_generate``: run during Otter Generate while all files are in-memory and before the
      the `tmp` directory is created
    - ``from_notebook``: run as students as they work through the notebook; see ``Notebook.run_plugin``
    - ``notebook_export``: run by ``Notebook.export`` for adding files to the export zip file
    - ``before_grading``: run before the submission is executed for altering configurations
    - ``before_execution``: run before the submission is executed for altering the submission
    - ``after_execution``: run after the submission is executed
    - ``after_grading``: run after all tests are run and scores are assigned
    - ``generate_report``: run after results are written

    See the docstring for the default implementation of each method for more information, including
    arguments and return values. If plugin has no actions for any event above, that method should raise
    ``otter.plugins.PluginEventNotSupportedException``. (This is the default behavior of this ABC, so
    inheriting from this class will do this for you for any methods you don't overwrite.)

    If this plugin requires metadata, it should be included in the plugin configuration of the 
    ``otter_config.json`` file as a subdictionary with key a key corresponding to the importable name
    of the plugin. If no configurations are required, the plugin name should be listed as a string.
    For example, the config below provides configurations for ``MyOtterPlugin`` but not 
    ``MyOtherOtterPlugin``.

    .. code-block:: json

        {
            "plugins": [
                {
                    "my_otter_plugin_package.MyOtterPlugin": {
                        "some_metadata_key": "some_value"
                    }
                },
                "my_otter_plugin_package.MyOtherOtterPlugin"
            ]
        }

    Args:
        submission_path (``str``): the absolute path to the submission being graded
        submission_metadata (``dict``): submission metadata; if on Gradescope, see
            https://gradescope-autograders.readthedocs.io/en/latest/submission_metadata/
        plugin_config (``dict``): configurations from the ``otter_config.json`` for this plugin, pulled
            from ``otter_config["plugins"][][PLUGIN_NAME]`` if ``otter_config["plugins"][]`` is a 
            ``dict``

    Attributes:
        submission_path (``str``): the absolute path to the submission being graded
        submission_metadata (``dict``): submission metadata; if on Gradescope, see
            https://gradescope-autograders.readthedocs.io/en/latest/submission_metadata/
        plugin_config (``dict``): configurations from the ``otter_config.json`` for this plugin, pulled
            from ``otter_config["plugins"][][PLUGIN_NAME]`` if ``otter_config["plugins"][]`` is a 
            ``dict``
    """

    def __init__(self, submission_path, submission_metadata, plugin_config):
        self.submission_path = submission_path
        self.submission_metadata = submission_metadata
        self.plugin_config = plugin_config

    def during_assign(self, assignment):
        """
        Plugin event run during the execution of Otter Assign after output directories are wrriten.
        Assignment configurations are passed in via the ``assignment`` argument.

        Args:
            assignment (``otter.assign.assignment.Assignment``): the ``Assignment`` instance with 
                configurations for the assignment; used similar to an ``AttrDict`` where keys are
                accessed with the dot syntax (e.g. ``assignment.master`` is the path to the master
                notebook)

        Raises:
            ``PluginEventNotSupportedException``: if the event is not supported by this plugin
        """
        raise PluginEventNotSupportedException()

    def during_generate(self, otter_config, assignment):
        """
        Plugin event run during the execution of Otter Generate that can modify the configurations
        to be written to ``otter_config.json``.

        Args:
            otter_config (``dict``): the dictionary of Otter configurations to be written to 
                ``otter_config.json`` in the zip file
            assignment (``otter.assign.assignment.Assignment``): the ``Assignment`` instance with 
                configurations for the assignment if Otter Assign was used to generate this zip file;
                will be set to ``None`` if Otter Assign is not being used

        Raises:
            ``PluginEventNotSupportedException``: if the event is not supported by this plugin
        """
        raise PluginEventNotSupportedException()

    def from_notebook(self, *args, **kwargs):
        """
        Plugin event run by students as they work through a notebook via the ``Notebook`` API (see
        ``Notebook.run_plugin``). Accepts arbitrary arguments and has no return.

        Args:
            *args: arguments for the plugin event
            **kwargs: keyword arguments for the plugin event

        Raises:
            ``PluginEventNotSupportedException``: if the event is not supported by this plugin
        """
        raise PluginEventNotSupportedException()
    
    def notebook_export(self, *args, **kwargs):
        """
        Plugin event run when a student calls ``Notebook.export``. Accepts arbitrary arguments and 
        should return a list of file paths to include in the exported zip file.

        Args:
            *args: arguments for the plugin event
            **kwargs: keyword arguments for the plugin event

        Returns:
            ``list[str]``: the list of file paths to include in the export

        Raises:
            ``PluginEventNotSupportedException``: if the event is not supported by this plugin
        """
        raise PluginEventNotSupportedException()

    def before_grading(self, options):
        """
        Plugin event run before the execution of the submission which can modify the dictionary of
        grading configurations.

        Args:
            options (``dict``): the dictionary of Otter configurations for grading

        Raises:
            ``PluginEventNotSupportedException``: if the event is not supported by this plugin
        """
        raise PluginEventNotSupportedException()

    def before_execution(self, submission):
        """
        Plugin event run before the execution of the submission which can modify the submission itself.
        This method should return a properly-formatted ``NotebookNode`` or string that will be executed in 
        place of the student's original submission.

        Args:
            submission (``nbformat.NotebookNode`` or ``str``): the submission for grading; if it is 
                a notebook, this will be the JSON-parsed ``dict`` of its contents; if it is a script, 
                this will be a string containing the code

        Returns:
            ``nbformat.NotebookNode`` or ``str``: the altered submission to be executed

        Raises:
            ``PluginEventNotSupportedException``: if the event is not supported by this plugin
        """
        raise PluginEventNotSupportedException()

    def after_execution(self, global_env):
        """
        Plugin event run after the execution of the submission which can modify the resulting global
        environment.

        Args:
            global_env (``dict``): the environment resulting from the execution of the students' code;
                see ``otter.execute``

        Raises:
            ``PluginEventNotSupportedException``: if the event is not supported by this plugin
        """
        raise PluginEventNotSupportedException()

    def after_grading(self, results):
        """
        Plugin event run after all tests are run on the resulting environment that gets passed the 
        ``otter.test_files.GradingResults`` object that stores the grading results for each test case.

        Args:
            results (``otter.test_files.GradingResults``): the results of all test cases

        Raises:
            ``PluginEventNotSupportedException``: if the event is not supported by this plugin
        """
        raise PluginEventNotSupportedException()

    def generate_report(self):
        """
        Plugin event run after grades are written to disk. This event should return a string that gets
        printed to stdout as a part of the plugin report.

        Returns:
            ``str``: the string to be included in the report

        Raises:
            ``PluginEventNotSupportedException``: if the event is not supported by this plugin
        """
        raise PluginEventNotSupportedException()
