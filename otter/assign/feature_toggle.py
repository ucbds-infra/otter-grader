"""Feature toggling for Otter Assign"""

from enum import Enum

from typing import Callable

from .assignment import Assignment


_NOT_RMD: Callable[[Assignment], bool] = lambda a: not a.is_rmd
"""a function that returns ``True`` if the assignment is not an R Markdown assignment"""


# TODO: move other things in
class FeatureToggle(Enum):
    """
    An enum for managing features that are enabled or disabled depending on the assignment config.
    """

    class FeatureToggleValue:

        test: Callable[[Assignment], bool]

        def __init__(self, test: Callable[[Assignment], bool]):
            self.test = test

        def is_enabled(self, assignment: Assignment):
            return self.test(assignment)

    PDF_FILTERING_COMMENTS = FeatureToggleValue(_NOT_RMD)
    """whether PDF filtering HTML comments should be inserted into the notebook"""

    EMPTY_MD_BOUNDARY_CELLS = FeatureToggleValue(_NOT_RMD)
    """whether to use empty Markdown cells for boundaries"""
