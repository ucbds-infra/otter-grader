"""Tests for ``otter.grade``"""

import logging
import os
import pandas as pd
import pytest
import re
import shutil
import zipfile

from contextlib import ExitStack
from glob import glob
from multiprocessing import Queue
from unittest import mock

from otter import logging
from otter.generate import main as generate
from otter.grade import main as grade
from otter.grade.utils import POINTS_POSSIBLE_LABEL
from otter.run import AutograderConfig
from otter.test_files import GradingResults

from ..utils import TestFileManager


ASSIGNMENT_NAME = "otter-grade-test"
FILE_MANAGER = TestFileManager(__file__)
AG_ZIP_PATH = FILE_MANAGER.get_path("autograder.zip")
ZIP_SUBM_PATH = "test/subm.zip"


@pytest.fixture(autouse=True)
def cleanup_output(cleanup_enabled):
    yield
    if cleanup_enabled:
        if os.path.exists("test/final_grades.csv"):
            os.remove("test/final_grades.csv")
        if os.path.exists("test/submission_pdfs"):
            shutil.rmtree("test/submission_pdfs")
        if os.path.exists(ZIP_SUBM_PATH):
            os.remove(ZIP_SUBM_PATH)
        if os.path.exists("test/grading-summaries"):
            shutil.rmtree("test/grading-summaries")


@pytest.fixture(autouse=True, scope="module")
def generate_zip_file():
    """
    Generate an autograder zip file for use in these tests.
    """
    generate(
        tests_dir=FILE_MANAGER.get_path("tests"),
        requirements=FILE_MANAGER.get_path("requirements.txt"),
        output_path=AG_ZIP_PATH,
        config=FILE_MANAGER.get_path("otter_config.json"),
        no_environment=True,
    )

    with logging.level_context(logging.DEBUG):
        yield

    if os.path.isfile(AG_ZIP_PATH):
        os.remove(AG_ZIP_PATH)


@pytest.fixture
def expected_points():
    test_points = {}
    for test_file in glob(FILE_MANAGER.get_path("tests/*.py")):
        env = {}
        with open(test_file) as f:
            exec(f.read(), env)

        test_points[env["test"]["name"]] = env["test"]["points"]

    return test_points


@pytest.mark.slow
@pytest.mark.docker
def test_timeout_some_notebooks_finish():
    """
    Check notebook ``1min.ipynb`` is killed due to exceeding the defined timeout while notebook ``10s.ipynb`` is graded;
    The final_grade.csv records everything correctly
    """
    grade_timeout = 30
    grade(
        name=ASSIGNMENT_NAME,
        paths=[FILE_MANAGER.get_path("timeout/")],
        output_dir="test/",
        autograder=AG_ZIP_PATH,
        containers=5,
        timeout=grade_timeout,
    )
    df_test = pd.read_csv("test/final_grades.csv")
    assert df_test.iloc[0]["grading_status"] == "--"
    assert df_test.iloc[1]["grading_status"] == "Completed"
    pattern = rf"Executing '[\w.\/-]*test\/test_grade\/files\/timeout\/1min\.ipynb' in docker container timed out in {grade_timeout} seconds"
    assert re.match(pattern, df_test.iloc[2]["grading_status"]) is not None


@pytest.mark.slow
@pytest.mark.docker
def test_timeout_no_notebooks_finish():
    """
    Check notebook ``1min.ipynb`` and ``10s.ipynb`` are killed due to exceeding the defined timeout;
    The final_grade.csv records everything correctly
    """
    grade_timeout = 5
    grade(
        name=ASSIGNMENT_NAME,
        paths=[FILE_MANAGER.get_path("timeout/")],
        output_dir="test/",
        autograder=AG_ZIP_PATH,
        containers=5,
        timeout=grade_timeout,
    )
    df_test = pd.read_csv("test/final_grades.csv")
    pattern1min = rf"Executing '[\w.\/-]*test\/test_grade\/files\/timeout\/1min\.ipynb' in docker container timed out in {grade_timeout} seconds"
    pattern10s = rf"Executing '[\w.\/-]*test\/test_grade\/files\/timeout\/10s\.ipynb' in docker container timed out in {grade_timeout} seconds"
    assert re.match(pattern10s, df_test.iloc[0]["grading_status"]) is not None
    assert re.match(pattern1min, df_test.iloc[1]["grading_status"]) is not None


@pytest.mark.slow
@pytest.mark.docker
def test_network(expected_points):
    """
    Check that the notebook ``network.ipynb`` is unable to do some network requests with disabled
    networking.
    """
    grade(
        name=ASSIGNMENT_NAME,
        paths=[FILE_MANAGER.get_path("network/")],
        output_dir="test/",
        autograder=AG_ZIP_PATH,
        containers=5,
        no_network=True,
    )

    df_test = pd.read_csv("test/final_grades.csv")

    # sort by filename
    df_test = df_test.sort_values("file").reset_index(drop=True)

    for _, row in df_test.iterrows():
        for test in expected_points:
            if "network.ipynb" == row["file"] and ("q2" in test or "q3" in test):
                assert row[test] == 0, "{} supposed to fail {} but passed".format(row["file"], test)
            else:
                assert (
                    row[test] == expected_points[test]
                ), "{} supposed to pass {} but failed".format(row["file"], test)


@pytest.mark.slow
@pytest.mark.docker
def test_notebooks_with_pdfs(expected_points):
    """
    Checks that notebooks are graded correctly and that PDFs are generated.
    """
    grade(
        name=ASSIGNMENT_NAME,
        paths=[FILE_MANAGER.get_path("notebooks/")],
        output_dir="test/",
        autograder=AG_ZIP_PATH,
        containers=5,
        pdfs=True,
    )

    # read the output and expected output
    df_test = pd.read_csv("test/final_grades.csv")

    # sort by filename
    df_test = df_test.sort_values("file").reset_index(drop=True)
    df_test["failures"] = df_test["file"].apply(
        lambda x: [int(n) for n in re.split(r"\D+", x) if len(n) > 0]
    )

    # add score sum cols for tests
    for test in expected_points:
        test_cols = [l for l in df_test.columns if bool(re.search(rf"\b{test}\b", l))]
        df_test[test] = df_test[test_cols].sum(axis=1)

    # check point values
    for _, row in df_test.iterrows():
        for test in expected_points:
            if int(re.sub(r"\D", "", test)) in row["failures"]:
                # q6.py has all_or_nothing set to False, so if the hidden tests fail you should get 2.5 points
                if "6H" in row["file"] and "q6" == test:
                    assert row[test] == 2.5, "{} supposed to fail {} but passed".format(
                        row["file"], test
                    )
                else:
                    assert row[test] == 0, "{} supposed to fail {} but passed".format(
                        row["file"], test
                    )
            else:
                assert (
                    row[test] == expected_points[test]
                ), "{} supposed to pass {} but failed".format(row["file"], test)

    assert os.path.exists("test/submission_pdfs"), "PDF folder is missing"

    # check that an pdf exists for each submission
    dir1_contents, dir2_contents = (
        [
            os.path.splitext(f)[0]
            for f in os.listdir(FILE_MANAGER.get_path("notebooks/"))
            if not (os.path.isdir(os.path.join(FILE_MANAGER.get_path("notebooks/"), f)))
        ],
        [
            os.path.splitext(f)[0]
            for f in os.listdir("test/submission_pdfs")
            if not (os.path.isdir(os.path.join("test/submission_pdfs", f)))
        ],
    )
    assert sorted(dir1_contents) == sorted(
        dir2_contents
    ), f"'{FILE_MANAGER.get_path('notebooks/')}' and 'test/submission_pdfs' have different contents"

    # check that the row with point totals for each question exists
    assert any(POINTS_POSSIBLE_LABEL in row for row in df_test.itertuples(index=False))


@mock.patch("otter.grade.launch_containers")
def test_single_notebook_grade(mocked_launch_grade):
    """
    Checks that when a single submission is passed to Otter Grade, it returns the percentage score.
    """
    notebook_path = FILE_MANAGER.get_path("notebooks/passesAll.ipynb")

    kw_expected = {
        "num_containers": 1,
        "base_image": "ubuntu:22.04",
        "tag": ASSIGNMENT_NAME,
        "no_kill": False,
        "pdf_dir": None,
        "timeout": None,
        "network": True,
        "config": AutograderConfig(),
    }

    gr = GradingResults([])
    mocked_launch_grade.return_value = [gr]

    with mock.patch(
        "otter.test_files.GradingResults.percent", new_callable=mock.PropertyMock
    ) as mocked_percent:
        mocked_percent.return_value = 0.9333

        output = grade(
            name=ASSIGNMENT_NAME,
            paths=[notebook_path],
            output_dir="test/",
            # the value of the autograder argument doesn't matter, it just needs to be a valid file path
            autograder=notebook_path,
            containers=1,
        )

    mocked_launch_grade.assert_called_with(notebook_path, [notebook_path], **kw_expected)
    assert output == 0.9333


@mock.patch("otter.grade.launch_containers")
def test_config_overrides(mocked_launch_grade):
    """
    Checks that the CLI flags are converted to config overrides correctly.
    """
    mocked_launch_grade.return_value = [GradingResults([])]

    notebook_path = FILE_MANAGER.get_path("notebooks/passesAll.ipynb")
    grade(
        name=ASSIGNMENT_NAME,
        paths=[notebook_path],
        output_dir="test/",
        # the value of the autograder argument doesn't matter, it just needs to be a valid file path
        autograder=notebook_path,
        containers=1,
        pdfs=True,
        ext="zip",
        debug=True,
    )

    assert mocked_launch_grade.call_args.kwargs["config"].get_user_config() == {
        "zips": True,
        "pdf": True,
        "debug": True,
    }


@pytest.mark.slow
@pytest.mark.docker
def test_config_overrides_integration():
    """
    Checks that overriding otter_config.json configurations with CLI flags works.
    """
    notebook_path = FILE_MANAGER.get_path("notebooks/passesAll.ipynb")
    with zipfile.ZipFile(ZIP_SUBM_PATH, "x") as zf:
        zf.write(notebook_path, arcname="passesAll.ipynb")

    output = grade(
        name=ASSIGNMENT_NAME,
        paths=[ZIP_SUBM_PATH],
        output_dir="test/",
        # the value of the autograder argument doesn't matter, it just needs to be a valid file path
        autograder=AG_ZIP_PATH,
        ext="zip",
    )

    assert output == 1.0

    got = pd.read_csv("test/final_grades.csv")
    want = pd.DataFrame(
        [
            {
                "q1": 0.0,
                "q2": 2.0,
                "q3": 2.0,
                "q4": 1.0,
                "q6": 5.0,
                "q2b": 2.0,
                "q7": 1.0,
                "percent_correct": 1,
                "total_points_earned": 13.0,
                "file": POINTS_POSSIBLE_LABEL,
                "grading_status": "--",
            },
            {
                "q1": 0.0,
                "q2": 2.0,
                "q3": 2.0,
                "q4": 1.0,
                "q6": 5.0,
                "q2b": 2.0,
                "q7": 1.0,
                "percent_correct": 1.0,
                "total_points_earned": 13.0,
                "file": os.path.basename(ZIP_SUBM_PATH),
                "grading_status": "Completed",
            },
        ]
    )

    # Sort the columns by label so the dataframes can be compared with ==.
    got = got.reindex(sorted(got.columns), axis=1)
    want = want.reindex(sorted(want.columns), axis=1)
    assert got.equals(want)


@mock.patch("otter.grade.launch_containers")
def test_grade_summaries(mocked_launch_grade):
    """
    Checks that are grading summaries are written to the disck
    """
    scores, mocks, expected = [], [], {}
    for filename in os.listdir(FILE_MANAGER.get_path("results")):
        with open(
            os.path.join(FILE_MANAGER.get_path("results"), filename), "r"
        ) as test_summary_file:
            summary = test_summary_file.read()

        expected[filename] = summary

        gr = GradingResults([])
        gr.file = os.path.splitext(filename)[0] + ".ipynb"
        mock_summary = mock.patch.object(gr, "summary")
        mocks.append((mock_summary, summary))

        scores.append(gr)

    mocked_launch_grade.return_value = scores

    notebook_path = FILE_MANAGER.get_path("notebooks")

    with ExitStack() as es:
        for m, s in mocks:
            es.enter_context(m).return_value = s

        grade(
            name=ASSIGNMENT_NAME,
            paths=[notebook_path],
            output_dir="test/",
            autograder=AG_ZIP_PATH,
            summaries=True,
        )

    assert sorted(os.listdir(FILE_MANAGER.get_path("results"))) == sorted(
        os.listdir("test/grading-summaries")
    )
    for filename in sorted(os.listdir("test/grading-summaries")):
        file_path = os.path.join("test/grading-summaries", filename)

        assert os.path.isfile(file_path)
        with open(file_path, "r") as summary_file:
            assert summary_file.read() == expected[filename], f"{filename} has diff"


@pytest.mark.slow
@pytest.mark.docker
def test_queue():
    """
    Checks that the queue is getting progress messages
    """
    notebook_path = FILE_MANAGER.get_path("notebooks/passesAll.ipynb")
    test_queue = Queue()
    logging.set_level(logging.INFO)
    grade(
        name=ASSIGNMENT_NAME,
        paths=[notebook_path],
        output_dir="test/",
        autograder=AG_ZIP_PATH,
        summaries=False,
        result_queue=test_queue,
    )
    with open(FILE_MANAGER.get_path("queue/passall_messages.txt"), "r") as f:
        for line in f:
            assert test_queue.get() == line.strip()
        assert test_queue.empty()
