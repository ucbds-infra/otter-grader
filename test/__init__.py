import os
import zipfile
import tempfile
import shutil
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

    def assertFilesEqual(self, p1, p2):
        try:
            with open(p1) as f1:
                with open(p2) as f2:
                    self.assertEqual(f1.read(), f2.read(), f"Contents of {p1} did not equal contents of {p2}")
        
        except UnicodeDecodeError:
            with open(p1, "rb") as f1:
                with open(p2, "rb") as f2:
                    self.assertEqual(f1.read(), f2.read(), f"Contents of {p1} did not equal contents of {p2}")

    def assertDirsEqual(self, dir1, dir2, ignore_ext=[], ignore_dirs=[]):
        self.assertTrue(os.path.exists(dir1), f"{dir1} does not exist")
        self.assertTrue(os.path.exists(dir2), f"{dir2} does not exist")
        self.assertTrue(os.path.isfile(dir1) == os.path.isfile(dir2), f"{dir1} and {dir2} have different type")

        if os.path.isfile(dir1):
            if os.path.splitext(dir1)[1] not in ignore_ext:
                self.assertFilesEqual(dir1, dir2)

        else:
            dir1_contents, dir2_contents = (
                [f for f in os.listdir(dir1) if not (os.path.isdir(os.path.join(dir1, f)) and f in ignore_dirs)], 
                [f for f in os.listdir(dir2) if not (os.path.isdir(os.path.join(dir2, f)) and f in ignore_dirs)], 
            )
            self.assertEqual(dir1_contents, dir2_contents, f"{dir1} and {dir2} have different contents")
            for f1, f2 in zip(dir1_contents, dir2_contents):
                f1, f2 = os.path.join(dir1, f1), os.path.join(dir2, f2)
                self.assertDirsEqual(f1, f2, ignore_ext=ignore_ext, ignore_dirs=ignore_dirs)

    def deletePaths(self, paths):
        for p in paths:
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.isfile(p):
                os.remove(p)
