"""
Grading plugins for Otter
"""

import importlib

from .abstract_plugin import AbstractOtterPlugin, PluginEventNotSupportedException


class PluginCollection:
    """
    """

    def __init__(self, plugin_names, submission_metadata, plugin_config):
        self._plugin_names = plugin_names
        self._plugins = None

        self._load_plugins(submission_metadata, plugin_config)

    def _load_plugins(self, submission_metadata, plugin_config):
        plugins = []
        for plg in self._plugin_names:
            module, class_ = ".".join(plg.split(".")[:-1]), plg.split(".")[-1]
            module = importlib.import_module(module)
            class_ = getattr(module, class_)

            # get the config key for the plugin
            plugin_cfg = plugin_config.get(class_.PLUGIN_CONFIG_KEY, {})
            plugin = class_(submission_metadata, plugin_cfg)
            plugins.append()

        self._plugins = plugins

    def run(self, event, *args, **kwargs):
        """
        """
        for plugin in self._plugins:
            try:
                if hasattr(plugin, event):
                    getattr(plugin, event)(plugin, *args, **kwargs)
            except PluginEventNotSupportedException:
                pass
