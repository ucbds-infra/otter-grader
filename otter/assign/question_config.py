"""Question configurations for Otter Assign"""

import fica

from typing import Any, Dict


class QuestionConfig(fica.Config):
    """
    """

    name = fica.Key(
        description="(required) the path to a requirements.txt file",
    )

    manual = fica.Key(
        description="whether this is a manually-graded question",
        default=False,
    )

    points = fica.Key(
        description="how many points this question is worth; defaults to 1 internally",
        default=None,
    )

    check_cell = fica.Key(
        description="whether to include a check cell after this question (for autograded questions only)",
        default=True,
    )

    export = fica.Key(
        description="whether to force-include this question in the exported PDF",
        default=False,
    )

    def __init__(self, user_config: Dict[str, Any] = {}):
        if "name" not in user_config:
            raise ValueError(f"Question name not specified: {user_config}")

        super().__init__(user_config)
