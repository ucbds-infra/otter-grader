"""Tests for ``otter.assign.utils``"""

import nbformat as nbf
import pytest

from otter.assign.utils import has_level_one_heading


@pytest.mark.parametrize(
    "source, expected",
    [
        ("# Homework 1", True),
        ("Some text\n\n# Homework 1", True),
        ("Homework 1\n==========", True),
        ("<h1>Homework 1</h1>", True),
        ("## Part 1", False),
        ("Homework 1\n----------", False),
        ("#hashtag", False),
        ("```python\n# a comment\n```", False),
        ("```\nnot a heading\n```\n===", False),
        ("", False),
    ],
)
def test_has_level_one_heading_markdown(source, expected):
    """
    Checks that level-one headings are detected in Markdown cells
    """
    assert has_level_one_heading(nbf.v4.new_markdown_cell(source)) is expected


def test_has_level_one_heading_other_cell_types():
    """
    Checks that only Markdown cells are considered
    """
    assert not has_level_one_heading(nbf.v4.new_code_cell("# Homework 1"))
    assert not has_level_one_heading(nbf.v4.new_raw_cell("# Homework 1"))
