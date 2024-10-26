"""Runner classes for different languages"""

from typing import Any

from ..autograder_config import AutograderConfig


def create_runner(otter_config: dict[str, Any], **kwargs: Any):
    """
    Return an instantiated runner for the assignment based on user-specified configurations.
    """
    config = AutograderConfig({**otter_config, **kwargs})

    if config.lang == "python":
        from .python_runner import PythonRunner

        return PythonRunner(config)
    elif config.lang == "r":
        from .r_runner import RRunner

        return RRunner(config)
    # There is no else required here because AutograderConfig validates that lang is one of the set
    # of possible values enumerated in the conditions above.
