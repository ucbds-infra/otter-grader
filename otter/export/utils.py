"""Utilities for Otter Export"""


class WkhtmltopdfNotFoundError(Exception):
    """
    Exception to throw when PDF via HTML is indicated but wkhtmltopdf is not found
    """
