"""Solution removal for Otter Assign for R notebooks"""

import copy
import re

from ..constants import MD_RESPONSE_CELL_SOURCE
from ..utils import get_source

solution_assignment_regex = re.compile(r"(\s*[\w. $()]*(=|<-))(.*) ?# ?SOLUTION")
def solution_assignment_sub(match):
    """
    Substitutes the first matching group  with ` ...`
    """
    prefix = match.group(1)
    return prefix + ' ...'


solution_line_regex = re.compile(r"(\s*).* ?# ?SOLUTION")
def solution_line_sub(match):
    """
    Substitutes the first matching group  with `# YOUR CODE HERE`
    """
    prefix = match.group(1)
    return prefix + '# YOUR CODE HERE'


SUBSTITUTIONS = [
    (solution_assignment_regex, solution_assignment_sub),
    (solution_line_regex, solution_line_sub),
]
