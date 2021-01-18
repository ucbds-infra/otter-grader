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
                {
                    "some_other_otter_plugin_package.SomeOtherOtterPlugin": {
                        "some_key": "some_value"
                    }
                }
            ]
        }

    Args:
        plugin_names (``list[Union[str,dict[str:Any]]]``): the importable names of plugin classes (e.g. 
            ``some_package.SomePlugin``) and their configurations
        submission_path (``str``): the absolute path to the submission being graded
        submission_metadata (``dict[str:Any]``): submission metadata
    """

    @staticmethod
    def _parse_plugin_config(plugin_config):
        if not isinstance(plugin_config, list):
            raise ValueError(f"Invalid plugin config: {plugin_config}")
        
        result = []
        for plg in plugin_config:
            if isinstance(plg, str):
                result.append({
                    "plugin": plg,
                    "config": {},
                })
            elif isinstance(plg, dict):
                keys = list(plg.keys())
                if not len(keys) == 1:
                    raise ValueError(f"Invalid plugin specification: {plg}")
                result.append({
                    "plugin": keys[0],
                    "config": plg[keys[0]],
                })

        return result

    def __init__(self, plugins, submission_path, submission_metadata):
        self._plugin_config = self._parse_plugin_config(plugins)
        self._plugins = None

        self._load_plugins(submission_path, submission_metadata)

    @property
    def _plugin_names(self):
        """
        The importable names of all of the plugins tracked
        """
        return [p["plugin"] for p in self._plugin_config]

    def _load_plugins(self, submission_path, submission_metadata):
        """
        Loads each plugin in ``self._plugin_config`` by importing it with ``importlib`` and creating
        and instance with the ``submission_metadata`` and the configurations from ``self._plugin_config``
        for that plugin. Sets ``self._plugins`` to be the list of imported and instantiated plugins.

        Args:
            submission_path (``str``): the absolute path to the submission being graded
            submission_metadata (``dict``): submission metadata
        """
        plugins = []
        for plg_cfg in self._plugin_config:
            plg, cfg = plg_cfg["plugin"], plg_cfg["config"]
            module, class_ = ".".join(plg.split(".")[:-1]), plg.split(".")[-1]
            module = importlib.import_module(module)
            class_ = getattr(module, class_)

            # get the config key for the plugin
            # plugin_cfg = plugin_config.get(class_.PLUGIN_CONFIG_KEY, {})
            plugin = class_(submission_path, submission_metadata, cfg)
            plugins.append(plugin)

        self._plugins = plugins

    def run(self, event, *args, **kwargs):
        """
        Runs the method ``event`` of each plugin in this collection. Passes ``args`` and ``kwargs``
        to this method. Ignores plugins that raise ``PluginEventNotSupportedException`` for this event.

        Args:
            event (``str``): name of the method of the plugin to run
            *args, **kwargs (any): arguments for the method
        
        Returns:
            ``list[Any]``: the values returned by each plugin for the called event
        """
        # TODO: logging to stdout
        rets = []
        for plugin in self._plugins:
            try:
                if hasattr(plugin, event):
                    ret = getattr(plugin, event)(*args, **kwargs)
                    rets.append(ret)
                else:
                    rets.append(None)
            except PluginEventNotSupportedException:
                rets.append(None)
        return rets

    def before_execution(self, submission):
        """
        Runs the ``before_execution`` event for each plugin, composing the results of each (i.e. the
        transformed notebook returned by one plugin is passed to the next plugin).

        Args:
            submission (``Union[str,nbformat.NotebookNode]``): the submission to be executed
        """
        event = "before_execution"
        for plugin in self._plugins:
            try:
                if hasattr(plugin, event):
                    submission = getattr(plugin, event)(submission)
            except PluginEventNotSupportedException:
                pass
        return submission

    def generate_report(self):
        """
        Runs the ``generate_report`` event of each plugin, formatting and concatenating them into a
        single string and returning it.

        Returns:
            ``str``: the plugin report
        """
        reports = self.run("generate_report")
        if not any(isinstance(r, str) for r in reports):
            return ""

        header = "=" * 35 + " PLUGIN REPORT " + "=" * 35
        footer = "=" * len(header)

        report = header
        for r, plg in zip(reports, self._plugin_names):
            if not isinstance(r, str):
                continue
            title = f" {plg} Report "
            dashes = len(header) - len(title)
            if dashes > 4:
                if dashes % 2 == 0:
                    ld, rd = dashes // 2, dashes // 2
                else:
                    ld, rd = dashes // 2, dashes // 2 + 1
            else:
                ld, rd = 2, 2

            title = "-" * ld + title + "-" * rd

            body = title + "\n" + r + "\n"

            report += "\n" + body
        
        report += "\n" + footer

        return report
