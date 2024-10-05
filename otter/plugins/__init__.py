"""
Grading plugins for Otter
"""

import importlib
import nbformat

from typing import Any, TypeVar, Union

from .abstract_plugin import AbstractOtterPlugin, PluginEventNotSupportedException
from ..utils import format_full_width


__all__ = ["AbstractOtterPlugin", "PluginCollection"]


_PluginConfigType = list[Union[str, dict[str, Any]]]
_SubmissionGenericType = TypeVar("_SubmissionGenericType", str, nbformat.NotebookNode)


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
        plugin_names (``list[str | dict[str, Any]]``): the importable names of plugin classes (e.g.
            ``some_package.SomePlugin``) and their configurations
        submission_path (``str``): the absolute path to the submission being graded
        submission_metadata (``dict[str, Any]``): submission metadata
    """

    _plugin_config: list[dict[str, Any]]
    """the parsed plugin configurations"""

    _plugins: list[AbstractOtterPlugin]
    """the initialized plugin instances"""

    _subm_path: str
    """the path to the submission file"""

    _subm_meta: dict[str, Any]
    """the submission metadata if running on Gradescope"""

    def __init__(
        self, plugins: _PluginConfigType, submission_path: str, submission_metadata: dict[str, Any]
    ):
        self._plugin_config = self._parse_plugin_config(plugins)

        self._subm_path = submission_path
        self._subm_meta = submission_metadata

        self._plugins = self._load_plugins(
            self._plugin_config, submission_path, submission_metadata
        )

    @staticmethod
    def _parse_plugin_config(plugin_config: _PluginConfigType) -> list[dict[str, Any]]:
        if not isinstance(plugin_config, list):
            raise ValueError(f"Invalid plugin config: {plugin_config}")

        result = []
        for plg in plugin_config:
            if isinstance(plg, str):
                result.append(
                    {
                        "plugin": plg,
                        "config": {},
                    }
                )
            elif isinstance(plg, dict):
                keys = list(plg.keys())
                if not len(keys) == 1:
                    raise ValueError(f"Invalid plugin specification: {plg}")
                result.append(
                    {
                        "plugin": keys[0],
                        "config": plg[keys[0]],
                    }
                )

        return result

    @property
    def _plugin_names(self) -> list[str]:
        """
        The importable names of all of the plugins tracked
        """
        return [p["plugin"] for p in self._plugin_config]

    @staticmethod
    def _load_plugins(
        plugin_config: _PluginConfigType, submission_path: str, submission_metadata: dict[str, Any]
    ) -> list[AbstractOtterPlugin]:
        """
        Loads each plugin in ``self._plugin_config`` by importing it with ``importlib`` and creating
        and instance with the ``submission_metadata`` and the configurations from ``self._plugin_config``
        for that plugin. Sets ``self._plugins`` to be the list of imported and instantiated plugins.

        Args:
            plugin_config (``list[str | dict[str, Any]]``): the plugin configurations
            submission_path (``str``): the absolute path to the submission being graded
            submission_metadata (``dict``): submission metadata

        Returns:
            ``list[AbstractOtterPlugin]``: the list of instantiated plugins
        """
        plugins = []
        for plg_cfg in plugin_config:
            plg, cfg = plg_cfg["plugin"], plg_cfg["config"]
            module, class_ = ".".join(plg.split(".")[:-1]), plg.split(".")[-1]
            module = importlib.import_module(module)
            class_ = getattr(module, class_)

            # get the config key for the plugin
            # plugin_cfg = plugin_config.get(class_.PLUGIN_CONFIG_KEY, {})
            plugin = class_(submission_path, submission_metadata, cfg)
            plugins.append(plugin)

        return plugins

    def add_new_plugins(self, raw_plugin_config: _PluginConfigType):
        """
        Add any new plugins specified in ``raw_plugin_config`` to this plugin collection. Any plugins
        listed that have already been isntatiated here are *not* added.

        Args:
            raw_plugin_config (``list[str | dict[str, Any]]``): the importable names of plugin
                classes (e.g. ``some_package.SomePlugin``) and their configurations
        """
        plg_cfg = self._parse_plugin_config(raw_plugin_config)
        for i, plg in list(enumerate(plg_cfg))[::-1]:
            if any(c["plugin"] == plg["plugin"] for c in self._plugin_config):
                plg_cfg.pop(i)

        self._plugin_config.extend(plg_cfg)
        self._plugins.extend(self._load_plugins(plg_cfg, self._subm_path, self._subm_meta))

    def run(self, event: str, *args: Any, **kwargs: Any):
        """
        Runs the method ``event`` of each plugin in this collection. Passes ``args`` and ``kwargs``
        to this method. Ignores plugins that raise ``PluginEventNotSupportedException`` for this
        event.

        Args:
            event (``str``): name of the method of the plugin to run
            *args, **kwargs (any): arguments for the method

        Returns:
            ``list[Any]``: the values returned by each plugin for the called event
        """
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

    def before_execution(self, submission: _SubmissionGenericType) -> _SubmissionGenericType:
        """
        Runs the ``before_execution`` event for each plugin, composing the results of each (i.e. the
        transformed notebook returned by one plugin is passed to the next plugin).

        Args:
            submission (``str | nbformat.NotebookNode``): the submission to be executed

        Returns:
            ``str | nbformat.NotebookNode``: the transformed submission
        """
        event = "before_execution"
        for plugin in self._plugins:
            try:
                if hasattr(plugin, event):
                    submission = getattr(plugin, event)(submission)
            except PluginEventNotSupportedException:
                pass
        return submission

    def generate_report(self) -> str:
        """
        Runs the ``generate_report`` event of each plugin, formatting and concatenating them into a
        single string and returning it.

        Returns:
            ``str``: the plugin report
        """
        reports = self.run("generate_report")
        if not any(isinstance(r, str) for r in reports):
            return ""

        # header = "=" * 35 + " PLUGIN REPORT " + "=" * 35
        header = format_full_width("=", mid_text="PLUGIN REPORT")
        footer = "=" * len(header)

        report = header
        for r, plg in zip(reports, self._plugin_names):
            if not isinstance(r, str):
                continue

            title = format_full_width("-", mid_text=f"{plg} Report")
            body = "\n" + title + "\n" + r + "\n"
            report += "\n" + body

        return report + "\n" + footer
