import os
import zipfile
import tempfile
import shutil
import subprocess
import unittest

from contextlib import contextmanager

class TestCase(unittest.TestCase):
    """
    Base class for Otter unit and integration tests that includes some helpful logging and custom 
    assert methods.
    """

    @classmethod
    def setUpClass(cls):
        print("\n" + ("=" * 70) + f"\nRunning Test Case {cls.__module__}.{cls.__name__}\ncwd: {os.getcwd()}\n" + ("=" * 70))
        return super().setUpClass()

    def setUp(self):
        print("\n" + ("-" * 70) + f"\nRunning {self.id()}\ncwd: {os.getcwd()}\n" + ("-" * 70))
        return super().setUp()

    @contextmanager
    def unzip_to_temp(self, zf_path, delete=False):
        tempdir = tempfile.mkdtemp()
        zf = zipfile.ZipFile(zf_path)
        zf.extractall(path=tempdir)
        zf.close()

        yield tempdir

        shutil.rmtree(tempdir)
        if delete:
            os.remove(zf_path)

    def create_docker_image(self):
        create_image_cmd = ["make", "docker-test"]
        subprocess.run(create_image_cmd, check=True)

    def assertFilesEqual(self, p1, p2, ignore_trailing_whitespace=True):
        try:
            with open(p1) as f1:
                with open(p2) as f2:
                    c1, c2 = f1.read(), f2.read()
                    if ignore_trailing_whitespace:
                        c1, c2 = c1.rstrip(), c2.rstrip()
                    self.assertEqual(c1, c2, f"Contents of {p1} did not equal contents of {p2}")
        
        except UnicodeDecodeError:
            with open(p1, "rb") as f1:
                with open(p2, "rb") as f2:
                    self.assertEqual(f1.read(), f2.read(), f"Contents of {p1} did not equal contents of {p2}")

    def assertDirsEqual(self, dir1, dir2, ignore_ext=[], ignore_dirs=[], variable_path_exts=[]):
        """
        Assert that the contents of two directories are equal recursively.

        Args:
            dir1 (``str``): the first directory
            dir1 (``str``): the second directory
            ignore_ext (``list[str]``, optional): a list of extensions for which the contents of any
                such files will not be compared when checking directories
            ignore_dirs (``list[str]``, optional): a list of directory names whose contents should
                be assumed to be the same (i.e. not to check)
            variable_path_exts(``list[str]``. optional): a list of extensions for paths whose stems
                may be different; if present, the number of files with these extensions is compared,
                although their contents and stems are ignored
        """
        self.assertTrue(os.path.exists(dir1), f"{dir1} does not exist")
        self.assertTrue(os.path.exists(dir2), f"{dir2} does not exist")
        self.assertTrue(os.path.isfile(dir1) == os.path.isfile(dir2), f"{dir1} and {dir2} have different type")
        
        if os.path.isfile(dir1):
            if os.path.splitext(dir1)[1] not in ignore_ext:
                self.assertFilesEqual(dir1, dir2)

        else:
            dir1_contents, dir2_contents = (
                [f for f in os.listdir(dir1) if not (os.path.isdir(os.path.join(dir1, f)) and f in ignore_dirs) \
                    and os.path.splitext(f)[1] not in variable_path_exts], 
                [f for f in os.listdir(dir2) if not (os.path.isdir(os.path.join(dir2, f)) and f in ignore_dirs) \
                    and os.path.splitext(f)[1] not in variable_path_exts], 
            )
            self.assertEqual(sorted(dir1_contents), sorted(dir2_contents), f"{dir1} and {dir2} have different contents")

            # check that for each variable path ext, there are the same number of files in each dir
            # with that ext
            for ext in variable_path_exts:
                self.assertEqual(
                    len([f for f in os.listdir(dir1) if os.path.splitext(f)[1] == ext]),
                    len([f for f in os.listdir(dir2) if os.path.splitext(f)[1] == ext]),
                    f"Variable path extension check failed for {dir1} and {dir2} with ext {ext}",
                )

            for f1, f2 in zip(dir1_contents, dir2_contents):
                f1, f2 = os.path.join(dir1, f1), os.path.join(dir2, f2)
                self.assertDirsEqual(f1, f2, ignore_ext=ignore_ext, ignore_dirs=ignore_dirs, 
                    variable_path_exts=variable_path_exts)

    def deletePaths(self, paths):
        for p in paths:
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.isfile(p):
                os.remove(p)
