"""Tests for ``otter.cli``"""

import os
import pytest

from click.testing import CliRunner
from unittest import mock

from otter.cli import cli


@pytest.fixture(scope="session")
def run_cli():
    """
    Create a function to invoke Otter's CLI with the specified command.

    Yields the function in the ``click.testing.CliRunner``'s ``isolated_filesystem`` context. This
    fixture is scoped for the test session, meaning only one instance of the ``CliRunner`` is ever
    created.

    Yields:
        ``callable[[list[str]], click.testing.Result]``: the function to invoke the CLI
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield lambda cmd: runner.invoke(cli, cmd)


def test_assign(run_cli):
    """
    Tests the ``otter assign`` CLI command.
    """
    master, result = "foo.ipynb", "dist"
    cmd_start = ["assign", master, result]

    open(master, "w+").close()

    std_kwargs = dict(
        master=master,
        result=result,
        no_run_tests=False,
        no_pdfs=False,
        username=None,
        password=None,
        debug=False,
        v0=False,
    )

    with mock.patch("otter.cli.assign") as mocked_assign:
        result = run_cli([*cmd_start])
        assert result.exit_code == 0
        mocked_assign.assert_called_with(**std_kwargs)

        result = run_cli([*cmd_start, "--no-run-tests"])
        assert result.exit_code == 0
        mocked_assign.assert_called_with(**{**std_kwargs, "no_run_tests": True})

        result = run_cli([*cmd_start, "--no-pdfs"])
        assert result.exit_code == 0
        mocked_assign.assert_called_with(**{**std_kwargs, "no_pdfs": True})

        un, pw = "foo", "bar"
        result = run_cli([*cmd_start, "--username", un, "--password", pw])
        assert result.exit_code == 0
        mocked_assign.assert_called_with(**{**std_kwargs, "username": un, "password": pw})

        result = run_cli([*cmd_start, "--debug"])
        assert result.exit_code == 0
        mocked_assign.assert_called_with(**{**std_kwargs, "debug": True})

        result = run_cli([*cmd_start, "--v0"])
        assert result.exit_code == 0
        mocked_assign.assert_called_with(**{**std_kwargs, "v0": True})

        # test invalid calls
        result = run_cli(["assign", "bar.ipynb", result])
        assert result.exit_code != 0

        os.mkdir("bar")
        result = run_cli(["assign", "bar", result])
        assert result.exit_code != 0

        result = run_cli(["assign", "foo.ipynb"])
        assert result.exit_code != 0
