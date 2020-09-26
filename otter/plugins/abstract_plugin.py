"""
Abstract base plugin class for Otter
"""

from abc import ABC, abstractmethod


class PluginEventNotSupportedException(Exception):
    """
    """


class AbstractOtterPlugin(ABC):
    """
    """

    PLUGIN_CONFIG_KEY = None

    def __init__(self, submission_metadata, plugin_config):
        self.submission_metadata = submission_metadata
        self.plugin_config = plugin_config

    def during_generate(self, otter_config):
        raise PluginEventNotSupportedException()

    def after_execution(self, global_env):
        raise PluginEventNotSupportedException()

    def after_grading(self, results):
        raise PluginEventNotSupportedException()

    def generate_report(self):
        raise PluginEventNotSupportedException()
