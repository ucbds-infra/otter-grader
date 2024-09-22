"""Utilities for Otter's testing suite"""

import nbformat as nbf
import os
import pathlib
import pprint
import pytest
import shutil
import subprocess
import tempfile
import zipfile

from contextlib import contextmanager

from otter.check.notebook import OTTER_LOG_FILENAME
from otter.test_files import OK_FORMAT_VARNAME


class TestFileManager:
    __test__ = False

    def __init__(self, test_file_path):
        self.dir = pathlib.Path(os.path.join(os.path.split(test_file_path)[0], "files"))

    def get_path(self, path):
        return str(self.dir / path)

    def open(self, path, *args, **kwargs):
        return open(self.get_path(path), *args, **kwargs)

    def assert_path_exists(self, path, file_okay=True, dir_okay=True):
        path = self.get_path(path)
        assert (
            os.path.exists(path)
            and (file_okay or os.path.isdir(path))
            and (dir_okay or os.path.isfile(path))
        )

    @classmethod
    def create_fixture(cls, file_dir):
        @pytest.fixture
        def file_manager():
            return cls(file_dir)

        return file_manager


def assert_notebooks_equal(p1, p2):
    nb1, nb2 = nbf.read(p1, as_version=nbf.NO_CONVERT), nbf.read(p2, as_version=nbf.NO_CONVERT)
    # ignore cell IDs
    for c in [*nb1.cells, *nb2.cells]:
        c.pop("id", None)
    diff = subprocess.run(
        ["diff", "--context=5", p1, p2],
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    assert nb1 == nb2, f"Contents of {p1} did not equal contents of {p2}:\n{diff}"


def assert_files_equal(p1, p2, ignore_trailing_whitespace=True):
    """
    Assert that two files have the same conentsly ignoring trailing whitespace.
    """
    assert os.path.splitext(p1)[1] == os.path.splitext(p2)[1]
    if os.path.splitext(p1)[1] == ".ipynb":
        assert_notebooks_equal(p1, p2)
        return
    try:
        with open(p1) as f1:
            with open(p2) as f2:
                c1, c2 = f1.read(), f2.read()
                if ignore_trailing_whitespace:
                    c1, c2 = c1.rstrip(), c2.rstrip()
                diff = subprocess.run(
                    ["diff", "--context=5", p1, p2],
                    stdout=subprocess.PIPE,
                ).stdout.decode("utf-8")
                assert c1 == c2, f"Contents of {p1} did not equal contents of {p2}:\n{diff}"

    except UnicodeDecodeError:
        with open(p1, "rb") as f1:
            with open(p2, "rb") as f2:
                assert f1.read() == f2.read(), f"Contents of {p1} did not equal contents of {p2}"


def assert_dirs_equal(
    dir1,
    dir2,
    ignore_ext=[],
    ignore_dirs=[],
    variable_path_exts=[],
    ignore_log=False,
):
    """
    Assert that the contents of two directories are equal recursively.

    Args:
        dir1 (``str``): the first directory
        dir1 (``str``): the second directory
        ignore_ext (``list[str]``): a list of extensions for which the contents of any
            such files will not be compared when checking directories
        ignore_dirs (``list[str]``): a list of directory names whose contents should
            be assumed to be the same (i.e. not to check)
        variable_path_exts(``list[str]``. optional): a list of extensions for paths whose stems
            may be different; if present, the number of files with these extensions is compared,
            although their contents and stems are ignored
    """
    assert os.path.exists(dir1), f"{dir1} does not exist"
    assert os.path.exists(dir2), f"{dir2} does not exist"
    assert os.path.isfile(dir1) == os.path.isfile(dir2), f"{dir1} and {dir2} have different type"

    if os.path.isfile(dir1):
        if os.path.splitext(dir1)[1] not in ignore_ext and (
            not ignore_log or os.path.split(dir1)[1] != OTTER_LOG_FILENAME
        ):
            assert_files_equal(dir1, dir2)

    else:
        dir1_contents, dir2_contents = (
            [
                f
                for f in os.listdir(dir1)
                if not (os.path.isdir(os.path.join(dir1, f)) and f in ignore_dirs)
                and os.path.splitext(f)[1] not in variable_path_exts
            ],
            [
                f
                for f in os.listdir(dir2)
                if not (os.path.isdir(os.path.join(dir2, f)) and f in ignore_dirs)
                and os.path.splitext(f)[1] not in variable_path_exts
            ],
        )
        assert sorted(dir1_contents) == sorted(
            dir2_contents
        ), f"{dir1} and {dir2} have different contents: {dir1_contents} != {dir2_contents}"

        # check that for each variable path ext, there are the same number of files in each dir
        # with that ext
        for ext in variable_path_exts:
            assert len([f for f in os.listdir(dir1) if os.path.splitext(f)[1] == ext]) == len(
                [f for f in os.listdir(dir2) if os.path.splitext(f)[1] == ext]
            ), f"Variable path extension check failed for {dir1} and {dir2} with ext {ext}"

        for f1, f2 in zip(dir1_contents, dir2_contents):
            f1, f2 = os.path.join(dir1, f1), os.path.join(dir2, f2)
            assert_dirs_equal(
                f1,
                f2,
                ignore_ext=ignore_ext,
                ignore_dirs=ignore_dirs,
                variable_path_exts=variable_path_exts,
                ignore_log=ignore_log,
            )


def delete_paths(paths, error_if_absent=False):
    for p in paths:
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.isfile(p):
            os.remove(p)
        elif error_if_absent:
            raise RuntimeError(f"Attempted to delete '{p}' but it does not exist")


@contextmanager
def unzip_to_temp(zf_path, delete_zip=False):
    tempdir = tempfile.mkdtemp()
    zf = zipfile.ZipFile(zf_path)
    zf.extractall(path=tempdir)
    zf.close()

    yield tempdir

    shutil.rmtree(tempdir)
    if delete_zip:
        os.remove(zf_path)


def write_ok_test(
    path,
    doctest,
    hidden=False,
    points=1,
    success_message=None,
    failure_message=None,
):
    test = {
        "name": os.path.splitext(os.path.basename(path))[0],
        "suites": [
            {
                "type": "doctest",
                "cases": [
                    {
                        "code": doctest,
                        "hidden": hidden,
                        "points": points,
                        "success_message": success_message,
                        "failure_message": failure_message,
                    }
                ],
            }
        ],
    }

    with open(path, "w+") as f:
        f.write(f"{OK_FORMAT_VARNAME} = True\n\ntest = ")
        pprint.pprint(test, f, indent=4, width=200, depth=None)
