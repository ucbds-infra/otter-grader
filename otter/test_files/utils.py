"""Utilities for Otter test files"""

import traceback


def get_traceback(excp):
    return "".join(traceback.format_exception(type(excp), excp, excp.__traceback__, limit=None))
