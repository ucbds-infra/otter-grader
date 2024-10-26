"""Solution removal for Otter Assign for R notebooks"""

import re


BLOCK_PROMPT = "# YOUR CODE HERE"


solution_assignment_regex = re.compile(r"(\s*[\w. $()]*(=|<-))(.*) ?# ?SOLUTION")


def solution_assignment_sub(match: re.Match[str]) -> str:
    """
    Substitutes the first matching group  with `` NULL # YOUR CODE HERE``
    """
    prefix = match.group(1)
    return prefix + " NULL # YOUR CODE HERE"


solution_line_regex = re.compile(r"(\s*).* ?# ?SOLUTION")


def solution_line_sub(match: re.Match[str]) -> str:
    """
    Substitutes the first matching group  with ``# YOUR CODE HERE``
    """
    prefix = match.group(1)
    return prefix + "# YOUR CODE HERE"


SUBSTITUTIONS = [
    (solution_assignment_regex, solution_assignment_sub),
    (solution_line_regex, solution_line_sub),
]
