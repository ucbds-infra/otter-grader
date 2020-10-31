"""
Grading plugins for Otter
"""

import importlib

from .abstract_plugin import AbstractOtterPlugin, PluginEventNotSupportedException


class PluginCollection:
    """
    Class for loading, organizing, and running plugins during grading. This class is instantiated with
    a list of plugin names, which should be importable strings that evaluate to objects that inherit 
    from ``otter.plugins.AbstractOtterPlugin``.

    When this class is instantiated, each plugin is imported and passed its configurations specified
    in the ``otter_config.json``. Plugins should be listed in ``otter_config.json`` in the ``plugins``
    key:

    .. code-block:: json

        {
            "plugins": [
                "some_otter_plugin_package.SomeOtterPlugin",
                "some_other_otter_plugin_package.SomeOtherOtterPlugin"
            ],
            "plugin_config: {}
        }

    Args:
        plugin_names (``list`` of ``str``): the importable names of plugin classes (e.g. 
            ``some_package.SomePlugin``)
        submission_metadata (``dict``): submission metadata
        plugin_config (``dict``): dictionary of configurations for all plugins
    """

    def __init__(self, plugin_names, submission_metadata, plugin_config):
        self._plugin_names = plugin_names
        self._plugins = None

        self._load_plugins(submission_metadata, plugin_config)

    def _load_plugins(self, submission_metadata, plugin_config):
        """
        Loads each plugin in ``self._plugin_names`` by importing it with ``importlib`` and creating
        and instance with the ``submission_metadata`` and the configurations from ``plugin_config``
        for that plugin. Sets ``self._plugins`` to be the list of imported and instantiated plugins.

        Args:
            submission_metadata (``dict``): submission metadata
            plugin_config (``dict``): dictionary of configurations for all plugins
        """
        plugins = []
        for plg in self._plugin_names:
            module, class_ = ".".join(plg.split(".")[:-1]), plg.split(".")[-1]
            module = importlib.import_module(module)
            class_ = getattr(module, class_)

            # get the config key for the plugin
            plugin_cfg = plugin_config.get(class_.PLUGIN_CONFIG_KEY, {})
            plugin = class_(submission_metadata, plugin_cfg)
            plugins.append(plugin)

        self._plugins = plugins

    def run(self, event, *args, **kwargs):
        """
        Runs the method ``event`` of each plugin in this collection. Passes ``args`` and ``kwargs``
        to this method. Ignores plugins that raise ``PluginEventNotSupportedException`` for this event.

        Args:
            event (``str``): name of the method of the plugin to run
            args, kwargs (any): arguments for the method
        """
        # TODO: logging to stdout
        for plugin in self._plugins:
            try:
                if hasattr(plugin, event):
                    getattr(plugin, event)(*args, **kwargs)
            except PluginEventNotSupportedException:
                pass
