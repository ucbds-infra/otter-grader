"""Utilities for Otter test files"""

import traceback


def get_traceback(excp):
    """
    Return the formatted traceback and message of an exception.

    Args:
        excp (``Exception``): the exception

    Returns:
        ``str``: the exception's traceback and message
    """
    return "".join(traceback.format_exception(type(excp), excp, excp.__traceback__, limit=None))
