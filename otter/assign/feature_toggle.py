""""""

from enum import Enum

from typing import Callable

from .assignment import Assignment


# TODO: refactor?
# TODO: move things in like check all cell
class FeatureToggle(Enum):
    """
    """

    class FeatureToggleValue:

        test: Callable[[Assignment], bool]

        def __init__(self, test: Callable[[Assignment], bool]):
            self.test = test

        def is_enabled(self, assignment: Assignment):
            return self.test(assignment)

    # TODO: allowed for R nbs? maybe enable because it should be harmless?
    PDF_FILTERING_COMMENTS = FeatureToggleValue(lambda a: not a.is_r)

    EMPTY_MD_BOUNDARY_CELLS = FeatureToggleValue(lambda a: not a.is_rmd)
