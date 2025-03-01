"""Utilities for Otter's testing suite"""

import nbformat as nbf
import os
import pathlib
import pprint
import pytest
import shutil
import tempfile
import zipfile

from contextlib import contextmanager

from otter.check.notebook import OTTER_LOG_FILENAME
from otter.test_files import OK_FORMAT_VARNAME


OUTPUT_DIR = pathlib.Path("test_output")
TEST_DIR = pathlib.Path("test").resolve()


class TestFileManager:
    __test__ = False

    def __init__(self, test_file_path):
        self.dir = pathlib.Path(os.path.join(os.path.split(test_file_path)[0], "files"))

    @property
    def path(self) -> str:
        return str(self.dir)

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


def update_goldens():
    for p in OUTPUT_DIR.rglob("*"):
        if not os.path.isfile(p):
            continue
        shutil.copy(p, TEST_DIR / pathlib.Path(*p.parts[1:]))


def save_test_output(got_file, golden_file):
    path = OUTPUT_DIR / pathlib.Path(golden_file).resolve().relative_to(TEST_DIR)
    os.makedirs(path.parent, exist_ok=True)
    shutil.copyfile(got_file, path)


def check_notebooks_equal(got_file, golden_file):
    nb1 = nbf.read(got_file, as_version=nbf.NO_CONVERT)
    nb2 = nbf.read(golden_file, as_version=nbf.NO_CONVERT)
    # ignore cell IDs
    for c in [*nb1.cells, *nb2.cells]:
        c.pop("id", None)
    ok = nb1 == nb2
    if not ok:
        save_test_output(got_file, golden_file)
    return ok


def check_files_equal(got_file, golden_file, ignore_trailing_whitespace=True):
    """
    Check that two files have the same conentsly ignoring trailing whitespace.
    """
    assert os.path.splitext(got_file)[1] == os.path.splitext(golden_file)[1]

    if os.path.splitext(got_file)[1] == ".ipynb":
        return check_notebooks_equal(got_file, golden_file)

    try:
        with open(got_file) as f1:
            with open(golden_file) as f2:
                c1, c2 = f1.read(), f2.read()
                if ignore_trailing_whitespace:
                    c1, c2 = c1.rstrip(), c2.rstrip()
                ok = c1 == c2

    except UnicodeDecodeError:
        with open(got_file, "rb") as f1:
            with open(golden_file, "rb") as f2:
                ok = f1.read() == f2.read()

    if not ok:
        save_test_output(got_file, golden_file)

    return ok


def assert_dirs_equal(
    output_dir,
    golden_dir,
    ignore_ext=[],
    ignore_dirs=[],
    variable_path_exts=[],
    ignore_log=False,
):
    """
    Assert that the contents of two directories are equal recursively.

    Args:
        output_dir (``str``): the directory produced by the test
        golden_dir (``str``): the golden directory
        ignore_ext (``list[str]``): a list of extensions for which the contents of any
            such files will not be compared when checking directories
        ignore_dirs (``list[str]``): a list of directory names whose contents should
            be assumed to be the same (i.e. not to check)
        variable_path_exts(``list[str]``. optional): a list of extensions for paths whose stems
            may be different; if present, the number of files with these extensions is compared,
            although their contents and stems are ignored
    """
    assert os.path.exists(output_dir), f"{output_dir} does not exist"
    assert os.path.exists(golden_dir), f"{golden_dir} does not exist"
    assert os.path.isfile(output_dir) == os.path.isfile(
        golden_dir
    ), f"{output_dir} and {golden_dir} have different type"

    if os.path.isfile(output_dir):
        if os.path.splitext(output_dir)[1] not in ignore_ext and (
            not ignore_log or os.path.split(output_dir)[1] != OTTER_LOG_FILENAME
        ):
            return check_files_equal(output_dir, golden_dir)

    else:
        output_dir_contents, golden_dir_contents = (
            sorted(
                [
                    f
                    for f in os.listdir(output_dir)
                    if not (os.path.isdir(os.path.join(output_dir, f)) and f in ignore_dirs)
                    and os.path.splitext(f)[1] not in variable_path_exts
                ]
            ),
            sorted(
                [
                    f
                    for f in os.listdir(golden_dir)
                    if not (os.path.isdir(os.path.join(golden_dir, f)) and f in ignore_dirs)
                    and os.path.splitext(f)[1] not in variable_path_exts
                ]
            ),
        )
        assert (
            output_dir_contents == golden_dir_contents
        ), f"{output_dir} and {golden_dir} have different contents: {output_dir_contents} != {golden_dir_contents}"

        # check that for each variable path ext, there are the same number of files in each dir
        # with that ext
        for ext in variable_path_exts:
            assert len([f for f in os.listdir(output_dir) if os.path.splitext(f)[1] == ext]) == len(
                [f for f in os.listdir(golden_dir) if os.path.splitext(f)[1] == ext]
            ), f"Variable path extension check failed for {output_dir} and {golden_dir} with ext {ext}"

        failures = []
        for f1, f2 in zip(output_dir_contents, golden_dir_contents):
            f1, f2 = os.path.join(output_dir, f1), os.path.join(golden_dir, f2)
            ok = assert_dirs_equal(
                f1,
                f2,
                ignore_ext=ignore_ext,
                ignore_dirs=ignore_dirs,
                variable_path_exts=variable_path_exts,
                ignore_log=ignore_log,
            )
            if not ok:
                failures.append(f1)

        failures_list = "- " + "\n- ".join(failures)
        assert not failures, f"{output_dir} has diff in files:\n{failures_list}"

    return True


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
