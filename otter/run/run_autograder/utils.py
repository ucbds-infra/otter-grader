"""Utilities for Otter Run"""


class OtterRuntimeError(RuntimeError):
    """
    A an error inheriting from ``RuntimeError`` for Otter to throw during a grading process.
    """


def add_quote_escapes(s):
    """
    Adds escape characters for quotes in a string.
    """
    new_s = ""
    for c in s:
        if c == '"':
            new_s += "\\"
        new_s += c
    return new_s
