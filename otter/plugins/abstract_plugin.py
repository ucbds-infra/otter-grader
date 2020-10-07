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

    - ``during_generate``: run during Otter Generate while all files are in-memory and before the
      the `tmp` directory is created
    - ``after_execution``: run after the submission is executed
    - ``after_grading``: run after all tests are run and scores are assigned
    - ``generate_report``: run after results are written

    See the docstring for the default implementation of each method for more information, including
    arguments and return values. If plugin has no actions for any event above, that method should raise
    ``otter.plugins.PluginEventNotSupportedException``. (This is the default behavior of this ABC, so
    inheriting from this class will do this for you for any methods you don't overwrite.)

    If this plugin requires metadata, it should be included in the ``plugin_config`` key of the 
    ``otter_config.json`` file as a subdictionary with key ``PLUGIN_CONFIG_KEY``. **You must set this
    class variable otherwise no metadata will be passed to the plugin.** For example, if 
    ``MyOtterPlugin.PLUGIN_CONFIG_KEY`` is ``my_otter_plugin``, the ``otter_config.json`` should look
    something like:

    .. code-block:: json

        {
            "plugins": [
                "my_otter_plugin_package.MyOtterPlugin``
            ]
            "plugin_config": {
                "my_otter_plugin": {
                    "some_metadata_key": "some_value"
                }
            }
        }

    Args:
        submission_metadata (``dict``): submission metadata; if on Gradescope, see
            https://gradescope-autograders.readthedocs.io/en/latest/submission_metadata/
        plugin_config (``dict``): configurations from the ``otter_config.json`` for this plugin, pulled
            from ``otter_config["plugin_config"][PLUGIN_CONFIG_KEY]``

    Attributes:
        submission_metadata (``dict``): submission metadata; if on Gradescope, see
            https://gradescope-autograders.readthedocs.io/en/latest/submission_metadata/
        plugin_config (``dict``): configurations from the ``otter_config.json`` for this plugin, pulled
            from ``otter_config["plugin_config"][PLUGIN_CONFIG_KEY]``
    """

    PLUGIN_CONFIG_KEY = None

    def __init__(self, submission_metadata, plugin_config):
        self.submission_metadata = submission_metadata
        self.plugin_config = plugin_config

    def during_generate(self, otter_config):
        """
        Plugin event run during the execution of Otter Generate that can modify the configurations
        to be written to ``otter_config.json``.

        Args:
            otter_config (``dict``): the dictionary of Otter configurations to be written to 
                ``otter_config.json`` in the zip file

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
