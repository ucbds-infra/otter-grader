"""Solution removal for Otter Assign for R notebooks"""

import copy
import re

from ..constants import MD_RESPONSE_CELL_SOURCE
from ..utils import get_source


def solution_assignment_sub(match):
    """
    Substitutes the first matching group  with ` NULL # YOUR CODE HERE`
    """
    prefix = match.group(1)
    return prefix + ' NULL # YOUR CODE HERE'


def solution_line_sub(match):
    """
    Substitutes the first matching group  with `# YOUR CODE HERE`
    """
    prefix = match.group(1)
    return prefix + '# YOUR CODE HERE'
