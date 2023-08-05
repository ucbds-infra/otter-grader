"""Tests for ``otter.generate.utils``"""

from otter.generate.utils import merge_conda_environments


def test_merge_conda_environments():
    e1 = {
        "name": "foo",
        "channels": ["c1", "c2"],
        "dependencies": [
            "d1",
            "d2>=1",
            "d3<=1",
            "d4=1",
            "d5<3",
            "d6>2",
            {
                "pip": [
                    "p1",
                    "p2==3.0.0",
                    "p3>=4",
                    "p4<=10",
                ],
            },
        ]
    }
    e2 = {
        "name": "bar",
        "channels": ["c1", "c3", "c4"],
        "dependencies": [
            "d1",
            "d2>=1",
            "d5<3",
            "d6<1",
            "d7",
            "d8>=10",
            {
                "pip": [
                    "p1",
                    "p2==4.0.0",
                    "p3>=4",
                    "p5",
                ],
            },
        ]
    }
    expected = {
        "name": "baz",
        "channels": ["c1", "c2", "c3", "c4"],
        "dependencies": [
            "d1",
            "d2>=1",
            "d3<=1",
            "d4=1",
            "d5<3",
            "d6>2",
            "d7",
            "d8>=10",
            {
                "pip": [
                    "p1",
                    "p2==3.0.0",
                    "p3>=4",
                    "p4<=10",
                    "p5",
                ],
            },
        ]
    }
    assert merge_conda_environments(e1, e2, "baz") == expected
