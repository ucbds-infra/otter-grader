"""Tests for ``otter.grade``"""

import logging
import os
import pandas as pd
import pytest
import re
import shutil
import subprocess
from unittest import mock
import zipfile

from glob import glob

from otter.generate import main as generate
from otter.generate.utils import zip_folder
from otter.grade import main as grade
from otter.grade.containers import launch_grade
from otter.utils import loggers

from .utils import TestFileManager


FILE_MANAGER = TestFileManager("test/test-grade")


@pytest.fixture(autouse=True)
def cleanup_output(cleanup_enabled):
    yield
    if cleanup_enabled:
        if os.path.exists("test/final_grades.csv"):
            os.remove("test/final_grades.csv")
        if os.path.exists("test/submission_pdfs"):
            shutil.rmtree("test/submission_pdfs")


def generate_autograder_zip(pdfs=False):
    generate(
        tests_dir = FILE_MANAGER.get_path("tests"), 
        requirements = FILE_MANAGER.get_path("requirements.txt"), 
        output_path = FILE_MANAGER.get_path("autograder.zip"),
        config = FILE_MANAGER.get_path("otter_config.json") if pdfs else None,
        no_environment = True,
    )
    with zipfile.ZipFile(FILE_MANAGER.get_path("autograder.zip"), "a") as zip_ref:
        zip_folder(zip_ref, os.getcwd(), exclude=[".git", "logo", "test", "dist", "build", "otter_grader.egg-info"])


@pytest.fixture(autouse=True, scope="module")
def create_docker_image():    
    subprocess.run(["make", "docker-grade-test"], check=True)

    shutil.copy("otter/grade/Dockerfile", "otter/grade/old-Dockerfile")
    with open("otter/grade/Dockerfile", "r+") as f:
        lines = f.readlines()

        idx = max([i if "ARG" in lines[i] else -1 for i in range(len(lines))])
        lines.insert(idx + 1, "ADD otter-grader /home/otter-grader\n")

        f.seek(0)
        f.write("".join(lines))

    generate_autograder_zip(pdfs=True)

    yield

    subprocess.run(["make", "cleanup-docker-grade-test"], check=True)

    if os.path.exists("otter/grade/old-Dockerfile"):
        os.remove("otter/grade/Dockerfile")
        shutil.move("otter/grade/old-Dockerfile", "otter/grade/Dockerfile")

    if os.path.isfile(FILE_MANAGER.get_path("autograder.zip")):
        os.remove(FILE_MANAGER.get_path("autograder.zip"))

    # prune images
    grade(prune=True, force=True)


@pytest.fixture
def expected_points():
    """
    Load in point values
    """
    test_points = {}
    for test_file in glob(FILE_MANAGER.get_path("tests/*.py")):
        env = {}
        with open(test_file) as f:
            exec(f.read(), env)

        test_points[env['test']['name']] = env['test']['points']

    return test_points


@pytest.mark.slow
@pytest.mark.docker
def test_docker():
    """
    Check that we have the right container installed and that docker is running
    """
    # use docker image inspect to see that the image is installed and tagged as otter-grader
    inspect = subprocess.run(
        ["docker", "image", "inspect", "otter-test"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # assert that it didn't fail, it will fail if it is not installed
    assert len(inspect.stderr) == 0, inspect.stderr.decode("utf-8")


@pytest.mark.slow
@pytest.mark.docker
def test_timeout():
    """
    Check that the notebook `20s.ipynb` is killed due to exceeding the defined timeout.
    """
    with pytest.raises(Exception, match=r"Executing '[\w./-]*test/test-grade/timeout/20s\.ipynb'" \
            " in docker container failed! Exit code: 137"), loggers.level_context(logging.DEBUG):
        grade(
            path=FILE_MANAGER.get_path("timeout/"),
            output_dir="test/",
            autograder=FILE_MANAGER.get_path("autograder.zip"),
            containers=5,
            image="otter-test",
            timeout=35,
        )


@pytest.mark.slow
@pytest.mark.docker
def test_network(expected_points):
    """
    Check that the notebook `network.ipynb` is unable to do some network requests with disabled networking
    """
    with loggers.level_context(logging.DEBUG):
        grade(
            path = FILE_MANAGER.get_path("network/"),
            output_dir = "test/",
            autograder = FILE_MANAGER.get_path("autograder.zip"),
            containers = 5,
            image = "otter-test",
            pdfs = True,
            no_network=True,
        )

    df_test = pd.read_csv("test/final_grades.csv")

    # sort by filename
    df_test = df_test.sort_values("file").reset_index(drop=True)

    for _, row in df_test.iterrows():
        for test in expected_points:
            if row['file'] == 'network.ipynb' and ('q2' in test or 'q3' in test):
                assert row[test] == 0, "{} supposed to fail {} but passed".format(row["file"], test)
            else:
                assert row[test] == expected_points[test], "{} supposed to pass {} but failed".format(row["file"], test)


@pytest.mark.slow
@pytest.mark.docker
def test_notebooks_with_pdfs(expected_points):
    """
    Check that the example of 100 notebooks runs correctely locally.
    """
    # grade the 100 notebooks
    with loggers.level_context(logging.DEBUG):
        grade(
            path = FILE_MANAGER.get_path("notebooks/"), 
            output_dir = "test/",
            autograder = FILE_MANAGER.get_path("autograder.zip"),
            containers = 5,
            image = "otter-test",
            pdfs = True,
        )

    # read the output and expected output
    df_test = pd.read_csv("test/final_grades.csv")

    # sort by filename
    df_test = df_test.sort_values("file").reset_index(drop=True)
    df_test["failures"] = df_test["file"].apply(lambda x: [int(n) for n in re.split(r"\D+", x) if len(n) > 0])

    # add score sum cols for tests
    for test in expected_points:
        test_cols = [l for l in df_test.columns if bool(re.search(fr"\b{test}\b", l))]
        df_test[test] = df_test[test_cols].sum(axis=1)

    # check point values
    for _, row in df_test.iterrows():
        for test in expected_points:
            if int(re.sub(r"\D", "", test)) in row["failures"]:
                # q6.py has all_or_nothing set to False, so if the hidden tests fail you should get 2.5 points
                if "6H" in row["file"] and "q6" == test:
                    assert row[test] == 2.5, "{} supposed to fail {} but passed".format(row["file"], test)
                else:
                    assert row[test] == 0, "{} supposed to fail {} but passed".format(row["file"], test)
            else:
                assert row[test] == expected_points[test], "{} supposed to pass {} but failed".format(row["file"], test)

    assert os.path.exists("test/submission_pdfs"), "PDF folder is missing"

    # check that an pdf exists for each submission
    dir1_contents, dir2_contents = (
        [os.path.splitext(f)[0] for f in os.listdir(FILE_MANAGER.get_path("notebooks/")) if not (os.path.isdir(os.path.join(FILE_MANAGER.get_path("notebooks/"), f)))],
        [os.path.splitext(f)[0] for f in os.listdir("test/submission_pdfs") if not (os.path.isdir(os.path.join("test/submission_pdfs", f)))],
    )
    assert sorted(dir1_contents) == sorted(dir2_contents), f"'{FILE_MANAGER.get_path('notebooks/')}' and 'test/submission_pdfs' have different contents"


def test_single_notebook_grade(expected_points):
    """
    Check that single notebook passed to grade returns percent.
    """
    data =  [{'q1': 2.0, 'q2':2.0, 'q3':2.0, 'q4':1.0, 'q6':5.0, \
                    'q2b':2.0, 'q7':1.0, 'percent_correct':1.0, 'file':'passesAll.ipynb'}]
    df = pd.DataFrame(data)
    notebook_path = FILE_MANAGER.get_path("notebooks/passesAll.ipynb")
    kw_expected = {
        "submissions_dir": mock.ANY,
        "num_containers": 1,
        "ext": 'ipynb',
        "no_kill": False,
        "output_path": 'test/',
        "zips": False,
        "image": 'otter-test',
        "pdfs": False,
        "timeout": None,
        "network": True
    }

    kws = {
        "path": notebook_path, 
        "output_dir": "test/",
        "autograder": notebook_path,
        "containers": 1,
        "image" : "otter-test",
        "pdfs" : False
    }

    with mock.patch("otter.grade.launch_grade") as mocked_launch_grade:
        mocked_launch_grade.return_value = [df]
        output = grade(**kws)
        mocked_launch_grade.assert_called_with(notebook_path, **kw_expected)
        assert output == 1.0


@mock.patch("otter.grade.containers.ThreadPoolExecutor")
@mock.patch("otter.grade.containers.build_image")
def test_changed_base_image(mocked_build_image, _):
    """
    Tests that changing the base image of a Docker container changes the resulting image's tag.
    """
    zip_path = FILE_MANAGER.get_path("autograder.zip")
    launch_grade(zip_path, "")
    launch_grade(zip_path, "", image="ubuntu")
    
    assert mocked_build_image.call_count == 2
    assert all(len(call.args) == 3 for call in mocked_build_image.call_args_list)
    assert mocked_build_image.call_args_list[0].args[2] != mocked_build_image.call_args_list[1].args[2]
