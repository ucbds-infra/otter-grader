"""Tests for ``otter.cli``"""

import os
import pytest
import re

from click.testing import CliRunner
from unittest import mock

from otter import __version__
from otter.cli import cli
from otter.generate import main as generate
from otter.grade import _ALLOWED_EXTENSIONS, main as grade


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


def test_verbosity(run_cli):
    """
    """
    # TODO


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


def test_generate(run_cli):
    """
    Tests the ``otter generate`` CLI command.
    """
    cmd_start = ["generate"]

    os.mkdir("tests")
    open("otter_config.json", "w+").close()
    open("requirements.txt", "w+").close()
    open("environment.yml", "w+").close()

    std_kwargs = dict(
        **generate.__kwdefaults__,
    )
    std_kwargs["files"] = tuple()
    std_kwargs.pop("assignment")
    std_kwargs.pop("plugin_collection")

    with mock.patch("otter.cli.generate") as mocked_generate:
        result = run_cli([*cmd_start])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**std_kwargs)

        os.mkdir("tests2")
        result = run_cli([*cmd_start, "-t", "tests2"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "tests_dir": "tests2"})

        result = run_cli([*cmd_start, "--tests-dir", "tests2"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "tests_dir": "tests2"})

        result = run_cli([*cmd_start, "-o", "output.zip"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "output_path": "output.zip"})

        result = run_cli([*cmd_start, "--output-path", "output.zip"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "output_path": "output.zip"})

        result = run_cli([*cmd_start, "-c", "otter_config.json"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "config": "otter_config.json"})

        result = run_cli([*cmd_start, "--config", "otter_config.json"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "config": "otter_config.json"})

        result = run_cli([*cmd_start, "--no-config"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "no_config": True})

        result = run_cli([*cmd_start, "-r", "requirements.txt"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "requirements": "requirements.txt"})

        result = run_cli([*cmd_start, "--requirements", "requirements.txt"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "requirements": "requirements.txt"})

        result = run_cli([*cmd_start, "--no-requirements"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "no_requirements": True})

        result = run_cli([*cmd_start, "-e", "environment.yml"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "environment": "environment.yml"})

        result = run_cli([*cmd_start, "--environment", "environment.yml"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "environment": "environment.yml"})

        result = run_cli([*cmd_start, "--no-environment"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "no_environment": True})

        result = run_cli([*cmd_start, "-l", "python"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "lang": "python"})

        result = run_cli([*cmd_start, "--lang", "r"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "lang": "r"})

        result = run_cli([*cmd_start, "--username", "foo", "--password", "bar"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "username": "foo", "password": "bar"})

        result = run_cli([*cmd_start, "--token", "abc123"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "token": "abc123"})

        result = run_cli([*cmd_start, "foo", "bar", "baz"])
        assert result.exit_code == 0
        mocked_generate.assert_called_with(**{**std_kwargs, "files": ("foo", "bar", "baz")})

        # test invalid calls
        result = run_cli(["generate", "-t", "tests3"])
        assert result.exit_code != 0

        result = run_cli(["generate", "-t", "otter_config.json"])
        assert result.exit_code != 0

        result = run_cli(["generate", "-c", "tests"])
        assert result.exit_code != 0

        result = run_cli(["generate", "-c", "bar.txt"])
        assert result.exit_code != 0

        result = run_cli(["generate", "-r", "tests"])
        assert result.exit_code != 0

        result = run_cli(["generate", "-r", "bar.txt"])
        assert result.exit_code != 0

        result = run_cli(["generate", "-e", "tests"])
        assert result.exit_code != 0

        result = run_cli(["generate", "-e", "bar.txt"])
        assert result.exit_code != 0

        result = run_cli(["generate", "-l", "bar"])
        assert result.exit_code != 0


def test_grade(run_cli):
    """
    Tests the ``otter grade`` CLI command.
    """
    cmd_start = ["grade"]

    open("autograder.zip", "wb+").close()

    std_kwargs = dict(
        **grade.__kwdefaults__,
    )

    with mock.patch("otter.cli.grade") as mocked_grade:
        result = run_cli([*cmd_start])
        assert result.exit_code == 0
        mocked_grade.assert_called_with(**std_kwargs)

        os.mkdir("notebooks")
        result = run_cli([*cmd_start, "-p", "notebooks"])
        assert result.exit_code == 0
        mocked_grade.assert_called_with(**{**std_kwargs, "path": "notebooks"})

        result = run_cli([*cmd_start, "--path", "notebooks"])
        assert result.exit_code == 0
        mocked_grade.assert_called_with(**{**std_kwargs, "path": "notebooks"})

        open("ag2.zip", "wb+").close()
        result = run_cli([*cmd_start, "-a", "ag2.zip"])
        assert result.exit_code == 0
        mocked_grade.assert_called_with(**{**std_kwargs, "autograder": "ag2.zip"})

        result = run_cli([*cmd_start, "--autograder", "ag2.zip"])
        assert result.exit_code == 0
        mocked_grade.assert_called_with(**{**std_kwargs, "autograder": "ag2.zip"})

        os.mkdir("output")
        result = run_cli([*cmd_start, "-o", "output"])
        assert result.exit_code == 0
        mocked_grade.assert_called_with(**{**std_kwargs, "output_dir": "output"})

        result = run_cli([*cmd_start, "--output-dir", "output"])
        assert result.exit_code == 0
        mocked_grade.assert_called_with(**{**std_kwargs, "output_dir": "output"})

        result = run_cli([*cmd_start, "-z"])
        assert result.exit_code == 0
        mocked_grade.assert_called_with(**{**std_kwargs, "zips": True})

        result = run_cli([*cmd_start, "--zips"])
        assert result.exit_code == 0
        mocked_grade.assert_called_with(**{**std_kwargs, "zips": True})

        for ext in _ALLOWED_EXTENSIONS:
            result = run_cli([*cmd_start, "--ext", ext])
            assert result.exit_code == 0
            mocked_grade.assert_called_with(**{**std_kwargs, "ext": ext})

        result = run_cli([*cmd_start, "--pdfs"])
        assert result.exit_code == 0
        mocked_grade.assert_called_with(**{**std_kwargs, "pdfs": True})

        



        # # test invalid calls
        # result = run_cli(["generate", "-t", "tests3"])
        # assert result.exit_code != 0

        # result = run_cli(["generate", "-t", "otter_config.json"])
        # assert result.exit_code != 0

        # result = run_cli(["generate", "-c", "tests"])
        # assert result.exit_code != 0

        # result = run_cli(["generate", "-c", "bar.txt"])
        # assert result.exit_code != 0

        # result = run_cli(["generate", "-r", "tests"])
        # assert result.exit_code != 0

        # result = run_cli(["generate", "-r", "bar.txt"])
        # assert result.exit_code != 0

        # result = run_cli(["generate", "-e", "tests"])
        # assert result.exit_code != 0

        # result = run_cli(["generate", "-e", "bar.txt"])
        # assert result.exit_code != 0

        # result = run_cli(["generate", "-l", "bar"])
        # assert result.exit_code != 0
