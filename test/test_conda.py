"""Tests that issues encountered in conda-forge builds don't recur."""

import subprocess
import sys


def test_otter_bin():
    """Tests that the ``otter`` binary works."""
    subprocess.run([sys.executable, "-m", "otter", "--help"], check=True)


def test_gmail_oauth2_bin():
    """Tests that the ``gmail_oauth2`` binary works."""
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "otter.plugins.builtin.gmail_notifications.bin.gmail_oauth2",
            "--help",
        ],
        check=True,
    )
