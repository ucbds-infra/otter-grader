"""Tests for ``otter.cli``"""

import os
import pytest
import re

from click.testing import CliRunner
from unittest import mock

from otter import __version__
from otter.cli import cli


@pytest.fixture()
def run_cli():
    """
    Create a function to invoke Otter's CLI with the specified command.

    Yields the function in the ``click.testing.CliRunner``'s ``isolated_filesystem`` context.

    Yields:
        ``callable[[list[str]], click.testing.Result]``: the function to invoke the CLI
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield lambda cmd: runner.invoke(cli, cmd)


def test_version(run_cli):
    """
    Tests the ``otter --version`` CLI command.
    """
    with mock.patch("otter.cli.print_version_info") as mocked_version:
        result = run_cli([])
        assert result.exit_code == 0
        mocked_version.assert_not_called()

        result = run_cli(["--version"])
        assert result.exit_code == 0
        mocked_version.assert_called_once_with(logo=True)


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


def test_check(run_cli):
    """
    Tests the ``otter check`` CLI command.
    """
    file = "foo.py"
    cmd_start = ["check", file]

    open(file, "w+").close()
    os.mkdir("tests")

    std_kwargs = dict(
        file=file,
        tests_path="./tests",
        question=None,
        seed=None,
    )

    with mock.patch("otter.cli.check") as mocked_check:
        result = run_cli([*cmd_start])
        assert result.exit_code == 0
        mocked_check.assert_called_with(**std_kwargs)

        result = run_cli([*cmd_start, "-q", "q1"])
        assert result.exit_code == 0
        mocked_check.assert_called_with(**{**std_kwargs, "question": "q1"})

        result = run_cli([*cmd_start, "--question", "q1"])
        assert result.exit_code == 0
        mocked_check.assert_called_with(**{**std_kwargs, "question": "q1"})

        os.mkdir("tests2")
        result = run_cli([*cmd_start, "-t", "tests2"])
        assert result.exit_code == 0
        mocked_check.assert_called_with(**{**std_kwargs, "tests_path": "tests2"})

        result = run_cli([*cmd_start, "--tests-path", "tests2"])
        assert result.exit_code == 0
        mocked_check.assert_called_with(**{**std_kwargs, "tests_path": "tests2"})

        result = run_cli([*cmd_start, "--seed", "1"])
        assert result.exit_code == 0
        mocked_check.assert_called_with(**{**std_kwargs, "seed": 1})

        # test invalid calls
        result = run_cli(["check"])
        assert result.exit_code != 0

        result = run_cli(["check", "tests2"])
        assert result.exit_code != 0

        result = run_cli(["check", file, "-t", "tests3"])
        assert result.exit_code != 0

        open("foo.txt", "w+").close()
        result = run_cli(["check", file, "-t", "foo.txt"])
        assert result.exit_code != 0
        assert re.search(
            r"Invalid value for '-t' / '--tests-path': Directory '.*' is a file\.", result.output)

        result = run_cli(["check", file, "--seed", "foo"])
        assert result.exit_code != 0
        assert "Error: Invalid value for '--seed': foo is not a valid integer" in result.output


def test_export(run_cli):
    """
    Tests the ``otter export`` CLI command.
    """
    src = "foo.ipynb"
    cmd_start = ["export", src]

    open(src, "w+").close()

    std_kwargs = dict(
        src=src,
        dest=None,
        exporter=None,
        filtering=False,
        pagebreaks=False,
        save=False,
        no_xecjk=False,
    )

    with mock.patch("otter.cli.export") as mocked_export:
        result = run_cli([*cmd_start])
        assert result.exit_code == 0
        mocked_export.assert_called_with(**std_kwargs)

        result = run_cli([*cmd_start, "foo.pdf"])
        assert result.exit_code == 0
        mocked_export.assert_called_with(**{**std_kwargs, "dest": "foo.pdf"})
        
        result = run_cli([*cmd_start, "--filtering"])
        assert result.exit_code == 0
        mocked_export.assert_called_with(**{**std_kwargs, "filtering": True})

        result = run_cli([*cmd_start, "--pagebreaks"])
        assert result.exit_code == 0
        mocked_export.assert_called_with(**{**std_kwargs, "pagebreaks": True})

        result = run_cli([*cmd_start, "-s"])
        assert result.exit_code == 0
        mocked_export.assert_called_with(**{**std_kwargs, "save": True})

        result = run_cli([*cmd_start, "--save"])
        assert result.exit_code == 0
        mocked_export.assert_called_with(**{**std_kwargs, "save": True})

        result = run_cli([*cmd_start, "--no-xecjk"])
        assert result.exit_code == 0
        mocked_export.assert_called_with(**{**std_kwargs, "no_xecjk": True})

        result = run_cli([*cmd_start, "-e", "latex"])
        assert result.exit_code == 0
        mocked_export.assert_called_with(**{**std_kwargs, "exporter": "latex"})

        result = run_cli([*cmd_start, "--exporter", "html"])
        assert result.exit_code == 0
        mocked_export.assert_called_with(**{**std_kwargs, "exporter": "html"})

        # test invalid calls
        result = run_cli(["export"])
        assert result.exit_code != 0

        result = run_cli(["export", "bar.ipynb"])
        assert result.exit_code != 0
        assert re.search(r"Error: Invalid value for 'SRC': File '.*' does not exist\.", result.output)

        os.mkdir("bar")
        result = run_cli(["export", "bar"])
        assert result.exit_code != 0
        assert re.search(r"Error: Invalid value for 'SRC': File '.*' is a directory\.", result.output)

        result = run_cli(["export", src, "-e", "foo"])
        assert result.exit_code != 0
        assert re.search(r"Error: Invalid value for '-e' / '--exporter': invalid choice: .*\. " \
            r"\(choose from latex, html\)", result.output)
