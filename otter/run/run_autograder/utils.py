"""Utilities for Otter Run"""


class OtterRuntimeError(RuntimeError):
    """
    A an error inheriting from ``RuntimeError`` for Otter to throw during a grading process.
    """


def add_quote_escapes(s):
    """
    Adds escape characters for quotes in a string.
    """
    new_s, last_c = "", ""
    for c in s:
        if c == '"' and last_c != "\\":
            new_s += "\\"
        new_s += c
        last_c = c
    return new_s
