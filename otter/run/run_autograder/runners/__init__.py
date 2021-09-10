"""Runner classes for different languages"""

from .abstract_runner import AbstractLanguageRunner


def create_runner(otter_config, **kwargs):
    """
    Return an instantiated runner for the assignment based on user-specified configurations.
    """
    lang = AbstractLanguageRunner.determine_language(otter_config, **kwargs)

    if lang == "python":
        from .python_runner import PythonRunner
        return PythonRunner(otter_config, **kwargs)
    elif lang == "r":
        from .r_runner import RRunner
        return RRunner(otter_config, **kwargs)
    else:
        raise ValueError("Unsupported language: {}".format(lang))
