"""Runner classes for different languages"""

from .abstract_runner import AbstractLanguageRunner
from .python_runner import PythonRunner
from .r_runner import RRunner


_LANGUAGE_RUNNERS = {
    "python": PythonRunner,
    "r": RRunner,
}


def create_runner(otter_config, **kwargs):
    """
    Return an instantiated runner for the assignment based on user-specified configurations.
    """
    lang = AbstractLanguageRunner.determine_language(otter_config, **kwargs)
    return _LANGUAGE_RUNNERS[lang.lower()](otter_config, **kwargs)
