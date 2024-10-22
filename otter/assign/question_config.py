"""Question configurations for Otter Assign"""

import fica

from typing import Any, Optional, Union


class QuestionConfig(fica.Config):
    """
    Configurations for a question.
    """

    name: str = fica.Key(
        description="(required) the path to a requirements.txt file",
    )

    manual: bool = fica.Key(
        description="whether this is a manually-graded question",
        default=False,
    )

    points: Union[int, float, None] = fica.Key(
        description="how many points this question is worth; defaults to 1 internally",
        default=None,
    )

    check_cell: bool = fica.Key(
        description="whether to include a check cell after this question (for autograded "
        "questions only)",
        default=True,
    )

    export: bool = fica.Key(
        description="whether to force-include this question in the exported PDF",
        default=False,
    )

    all_or_nothing: bool = fica.Key(
        description="whether points should be assigned on an all-or-nothing basis",
        default=False,
    )

    def __init__(
        self,
        user_config: Optional[dict[str, Any]] = None,
        documentation_mode: bool = False,
        **kwargs,
    ):
        if user_config is None:
            user_config = {}
        if "name" not in user_config and not documentation_mode:
            raise ValueError(f"Question name not specified: {user_config}")

        super().__init__(user_config=user_config, documentation_mode=documentation_mode, **kwargs)
