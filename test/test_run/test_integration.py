"""Tests for ``otter.run``"""

import copy
import dill
import json
import nbconvert
import nbformat
import os
import pathlib
import pytest
import re
import shutil
import zipfile

from contextlib import contextmanager, nullcontext
from textwrap import dedent
from unittest import mock

from otter.generate.token import APIClient
from otter.run import main as run_main


try:
    from otter.run.run_autograder import main as run_autograder
except ModuleNotFoundError as e:
    if "'otter'" in str(e):
        raise RuntimeError(
            "The 'otter' module could not be imported. This is usually caused by errors while building the "
            "grading image, so check the image build logs and include them when requesting "
            "support."
        )
    raise e
from otter.run.run_autograder.utils import OtterRuntimeError
from otter.test_files import GradingResults
from otter.utils import chdir, NBFORMAT_VERSION

from ..utils import delete_paths, TestFileManager


FILE_MANAGER = TestFileManager(__file__)


@pytest.fixture(autouse=True)
def cleanup_output(cleanup_enabled):
    with FILE_MANAGER.open("autograder/source/otter_config.json") as f:
        cpy = f.read()
    with FILE_MANAGER.open("rmd-autograder/source/otter_config.json") as f:
        crmd = f.read()
    yield
    if cleanup_enabled:
        delete_paths(
            [
                FILE_MANAGER.get_path("autograder/results/results.json"),
                FILE_MANAGER.get_path("autograder/results/results.pkl"),
                FILE_MANAGER.get_path("autograder/__init__.py"),
                FILE_MANAGER.get_path("autograder/submission/test"),
                FILE_MANAGER.get_path("autograder/submission/tests"),
                FILE_MANAGER.get_path("autograder/submission/fails2and6H.pdf"),
                FILE_MANAGER.get_path("autograder/submission/__init__.py"),
                FILE_MANAGER.get_path("autograder/submission/.OTTER_LOG"),
                FILE_MANAGER.get_path("rmd-autograder/results/results.json"),
                FILE_MANAGER.get_path("rmd-autograder/results/results.pkl"),
                FILE_MANAGER.get_path("rmd-autograder/__init__.py"),
                FILE_MANAGER.get_path("rmd-autograder/submission/test"),
                FILE_MANAGER.get_path("rmd-autograder/submission/tests"),
                FILE_MANAGER.get_path("rmd-autograder/submission/__init__.py"),
                FILE_MANAGER.get_path("rmd-autograder/submission/.OTTER_LOG"),
                FILE_MANAGER.get_path("results.json"),
            ]
        )
        with FILE_MANAGER.open("autograder/source/otter_config.json", "w") as f:
            f.write(cpy)
        with FILE_MANAGER.open("rmd-autograder/source/otter_config.json", "w") as f:
            f.write(crmd)


@pytest.fixture(autouse=True)
def correct_cwd_on_exit():
    cwd = os.getcwd()
    yield
    os.chdir(cwd)


@pytest.fixture
def expected_results():
    return {
        "tests": [
            {
                "name": "Public Tests",
                "visibility": "visible",
                "output": "q1 results: All test cases passed!\n\nq2 results:\n    q2 - 1 result:\n        ❌ Test case failed\n        Trying:\n            negate(True)\n        Expecting:\n            False\n        **********************************************************************\n        Line 2, in q2 0\n        Failed example:\n            negate(True)\n        Expected:\n            False\n        Got:\n            True\n\n    q2 - 2 result:\n        ❌ Test case failed\n        Trying:\n            negate(False)\n        Expecting:\n            True\n        **********************************************************************\n        Line 2, in q2 1\n        Failed example:\n            negate(False)\n        Expected:\n            True\n        Got:\n            False\n\nq3 results: All test cases passed!\n\nq4 results: All test cases passed!\n\nq6 results: All test cases passed!\n\nq7 results: All test cases passed!",
                "status": "failed",
            },
            {
                "name": "q1",
                "score": 0.0,
                "max_score": 0.0,
                "visibility": "hidden",
                "output": "q1 results: All test cases passed!",
            },
            {
                "name": "q2",
                "score": 0,
                "max_score": 2.0,
                "visibility": "hidden",
                "output": 'q2 results:\n    q2 - 1 result:\n        ❌ Test case failed\n        Trying:\n            negate(True)\n        Expecting:\n            False\n        **********************************************************************\n        Line 2, in q2 0\n        Failed example:\n            negate(True)\n        Expected:\n            False\n        Got:\n            True\n\n    q2 - 2 result:\n        ❌ Test case failed\n        Trying:\n            negate(False)\n        Expecting:\n            True\n        **********************************************************************\n        Line 2, in q2 1\n        Failed example:\n            negate(False)\n        Expected:\n            True\n        Got:\n            False\n\n    q2 - 3 result:\n        ❌ Test case failed\n        Trying:\n            negate("")\n        Expecting:\n            True\n        **********************************************************************\n        Line 2, in q2 2\n        Failed example:\n            negate("")\n        Expected:\n            True\n        Got:\n            \'\'\n\n    q2 - 4 result:\n        ❌ Test case failed\n        Trying:\n            negate(1)\n        Expecting:\n            False\n        **********************************************************************\n        Line 2, in q2 3\n        Failed example:\n            negate(1)\n        Expected:\n            False\n        Got:\n            1',
            },
            {
                "name": "q3",
                "score": 2.0,
                "max_score": 2.0,
                "visibility": "hidden",
                "output": "q3 results: All test cases passed!",
            },
            {
                "name": "q4",
                "score": 1.0,
                "max_score": 1.0,
                "visibility": "hidden",
                "output": "q4 results: All test cases passed!",
            },
            {
                "name": "q6",
                "score": 2.5,
                "max_score": 5.0,
                "visibility": "hidden",
                "output": "q6 results:\n    q6 - 1 result:\n        ✅ Test case passed\n\n    q6 - 2 result:\n        ❌ Test case failed\n        Trying:\n            fib = fiberator()\n        Expecting nothing\n        ok\n        Trying:\n            for _ in range(10):\n                print(next(fib))\n        Expecting:\n            0\n            1\n            1\n            2\n            3\n            5\n            8\n            13\n            21\n            34\n        **********************************************************************\n        Line 3, in q6 1\n        Failed example:\n            for _ in range(10):\n                print(next(fib))\n        Expected:\n            0\n            1\n            1\n            2\n            3\n            5\n            8\n            13\n            21\n            34\n        Got:\n            0\n            1\n            1\n            1\n            2\n            3\n            5\n            8\n            13\n            21",
            },
            {
                "name": "q7",
                "score": 1.0,
                "max_score": 1.0,
                "visibility": "hidden",
                "output": "q7 results: All test cases passed!",
            },
        ],
        "output": "Students are allowed 1 submissions every 1 days. You have 0 submissions in that period.",
    }


@pytest.fixture(scope="module")
def expected_rmd_results():
    return {
        "tests": [
            {
                "name": "Public Tests",
                "output": "q1 results: All test cases passed!",
                "visibility": "visible",
                "status": "passed",
            },
            {
                "max_score": 5,
                "name": "q1",
                "output": "q1 results: All test cases passed!\nq1d message: congrats",
                "score": 5,
                "visibility": "hidden",
            },
        ],
    }


@contextmanager
def alternate_config(config_path, new_config):
    with open(config_path) as f:
        contents = f.read()
    with open(config_path, "w") as f:
        json.dump(new_config, f)
    try:
        yield
    finally:
        with open(config_path, "w") as f:
            f.write(contents)


def get_expected_error_results(error):
    return {
        "score": 0,
        "stdout_visibility": "hidden",
        "tests": [
            {
                "name": "Autograder Error",
                "output": f"Otter encountered an error when grading this submission:\n\n{error}",
            },
        ],
    }


@contextmanager
def alternate_submission(subm_path, new_nb):
    with open(subm_path) as f:
        contents = f.read()
    nbformat.write(new_nb, subm_path)
    try:
        yield
    finally:
        with open(subm_path, "w") as f:
            f.write(contents)


@contextmanager
def alternate_tests(test_files):
    src, dst = FILE_MANAGER.get_path("autograder/source/tests"), FILE_MANAGER.get_path(
        "autograder/source/tests_orig"
    )
    os.rename(src, dst)
    os.makedirs(src, exist_ok=True)
    for fn, contents in test_files.items():
        with open(os.path.join(src, fn), "w+") as f:
            f.write(contents)
    try:
        yield
    finally:
        shutil.rmtree(src)
        os.rename(dst, src)


@pytest.fixture(autouse=True)
def mock_export_notebook(cleanup_enabled):
    empty_pdfs = []

    def make_empty_pdf(*args, **kwargs):
        p = kwargs["dest"]
        open(p, "wb+").close()
        empty_pdfs.append((os.getcwd(), p))

    with mock.patch(
        "otter.run.run_autograder.runners.python_runner.export_notebook"
    ) as mocked_export_notebook:
        mocked_export_notebook.side_effect = make_empty_pdf
        yield mocked_export_notebook

    if not cleanup_enabled:
        return

    for wd, p in empty_pdfs:
        full_path = os.path.join(wd, p)
        if os.path.exists(full_path):
            os.remove(full_path)


@pytest.fixture
def get_config_path():
    def do_get_config_path(rmd=False):
        dirname = "autograder" if not rmd else "rmd-autograder"
        return FILE_MANAGER.get_path(f"{dirname}/source/otter_config.json")

    return do_get_config_path


@pytest.fixture
def load_config(get_config_path):
    def load_config_file(rmd=False):
        with open(get_config_path(rmd=rmd)) as f:
            return json.load(f)

    return load_config_file


@mock.patch("otter.run.tempfile")
@mock.patch("otter.run.run_autograder_main")
def test_otter_run_main(mocked_run_autograder_main, mocked_tempfile, tmp_path):
    """Tests ``otter.run.main``."""
    zf_path = tmp_path / "autograder.zip"
    with zipfile.ZipFile(zf_path, mode="w") as zf:
        zf.writestr("a_file", "ooh-ee-ooh-ah-ah-ting-tang-walla-walla-bing-bang")

    subm_path = tmp_path / "submission.ipynb"
    with open(subm_path, "w+") as f:
        f.write("I told the witch doctor you didn't love me true")

    def check_dir_contents(ag_path, *args, **kwargs):
        with chdir(ag_path):
            for subdir in ["source", "submission", "results"]:
                assert os.path.isdir(subdir)

            assert os.listdir("source") == ["a_file"]
            assert (
                pathlib.Path("source/a_file").read_text()
                == "ooh-ee-ooh-ah-ah-ting-tang-walla-walla-bing-bang"
            )

            assert os.listdir("submission") == ["submission.ipynb"]
            assert (
                pathlib.Path("submission/submission.ipynb").read_text()
                == "I told the witch doctor you didn't love me true"
            )

            assert os.path.isfile("submission_metadata.json")

            # write output files
            with open("results/results.json", "w+") as f:
                f.write('{"ooh": "ee"}')

            with open("results/results.pkl", "wb+") as f:
                dill.dump(GradingResults([]), f)

    # use the mock's side effect function to check that the autograder directory was set up
    # correctly
    mocked_run_autograder_main.side_effect = check_dir_contents
    mocked_tempfile.mkdtemp.return_value = str(tmp_path / "autograder_dir")

    res = run_main(str(subm_path), autograder=str(zf_path), output_dir=FILE_MANAGER.path)

    mocked_run_autograder_main.assert_called_once_with(
        str(tmp_path / "autograder_dir" / "autograder"), logo=True, debug=False, otter_run=True
    )
    assert isinstance(res, GradingResults)
    assert open(FILE_MANAGER.get_path("results.json")).read() == '{"ooh": "ee"}'


def test_notebook(load_config, expected_results):
    config = load_config()
    run_autograder(config["autograder_dir"])

    with FILE_MANAGER.open("autograder/results/results.json") as f:
        actual_results = json.load(f)

    assert (
        actual_results == expected_results
    ), f"Actual results did not matched expected:\n{actual_results}"


@mock.patch("otter.run.run_autograder.runners.python_runner.export_notebook")
def test_pdf_generation_failure(mocked_export, get_config_path, load_config, expected_results):
    config = load_config()
    config["warn_missing_pdf"] = True
    config["token"] = "abc123"

    expected_results["tests"].insert(
        1,
        {
            "name": "PDF Generation Failed",
            "visibility": "visible",
            "output": "nu-uh",
            "status": "failed",
        },
    )

    with alternate_config(get_config_path(), config):
        mocked_export.side_effect = ValueError("nu-uh")
        run_autograder(config["autograder_dir"])

    with FILE_MANAGER.open("autograder/results/results.json") as f:
        actual_results = json.load(f)

    assert (
        actual_results == expected_results
    ), f"Actual results did not matched expected:\n{actual_results}"


@mock.patch.object(APIClient, "upload_pdf_submission")
@mock.patch("otter.run.run_autograder.runners.python_runner.export_notebook")
def test_use_submission_pdf(
    mocked_export,
    mocked_upload_pdf_submission,
    get_config_path,
    load_config,
    expected_results,
):
    config = load_config()
    config["use_submission_pdf"] = True
    config["token"] = "abc123"

    FILE_MANAGER.open("autograder/submission/fails2and6H.pdf", "wb+").close()

    with alternate_config(get_config_path(), config):
        run_autograder(config["autograder_dir"])

    with FILE_MANAGER.open("autograder/results/results.json") as f:
        actual_results = json.load(f)

    mocked_export.assert_not_called()
    mocked_upload_pdf_submission.assert_called_with(
        config["course_id"],
        config["assignment_id"],
        "student@univ.edu",  # from submission_metadata.json in autograder dir
        "fails2and6H.pdf",
    )
    assert (
        actual_results == expected_results
    ), f"Actual results did not matched expected:\n{actual_results}"


def test_force_public_test_summary(get_config_path, load_config):
    def perform_test(show_hidden, force_public_test_summary, expect_summary):
        config = load_config()
        config["show_hidden"] = show_hidden
        config["force_public_test_summary"] = force_public_test_summary
        with alternate_config(get_config_path(), config):
            run_autograder(config["autograder_dir"])

        with FILE_MANAGER.open("autograder/results/results.json") as f:
            actual_results = json.load(f)

        message = f"show_hidden={show_hidden}, force_public_test_summary={force_public_test_summary}, expect_summary={expect_summary}"
        if expect_summary:
            assert actual_results["tests"][0]["name"] == "Public Tests", message
        else:
            assert actual_results["tests"][0]["name"] != "Public Tests", message

    perform_test(False, False, True)
    perform_test(False, True, True)
    perform_test(True, False, False)
    perform_test(True, True, True)


def test_script(load_config, expected_results, get_config_path):
    config = load_config()
    nb_path = FILE_MANAGER.get_path("autograder/submission/fails2and6H.ipynb")
    nb = nbformat.read(nb_path, as_version=NBFORMAT_VERSION)

    # Remove the token so that we don't try to generate a PDF of a script.
    config.pop("token")

    try:
        py, _ = nbconvert.export(nbconvert.PythonExporter, nb)

        # remove magic commands
        py = "\n".join(l for l in py.split("\n") if not l.startswith("get_ipython"))

        os.remove(nb_path)
        with FILE_MANAGER.open("autograder/submission/fails2and6H.py", "w+") as f:
            f.write(py)

        with alternate_config(get_config_path(), config):
            run_autograder(config["autograder_dir"])

        with FILE_MANAGER.open("autograder/results/results.json") as f:
            actual_results = json.load(f)

        assert (
            actual_results == expected_results
        ), f"Actual results did not matched expected:\n{actual_results}"

    finally:
        delete_paths([FILE_MANAGER.get_path("autograder/submission/fails2and6H.py")])
        with open(nb_path, "w+") as f:
            nbformat.write(nb, f)


def test_assignment_name(load_config, expected_results):
    name = "hw01"
    config = load_config()
    nb_path = FILE_MANAGER.get_path("autograder/submission/fails2and6H.ipynb")
    orig_nb = nbformat.read(nb_path, as_version=NBFORMAT_VERSION)
    nb = copy.deepcopy(orig_nb)

    def perform_test(nb, expected_results, error=None, **kwargs):
        nbformat.write(nb, nb_path)

        cm = (
            pytest.raises(OtterRuntimeError, match=re.escape(error))
            if error is not None
            else nullcontext()
        )
        with cm:
            run_autograder(config["autograder_dir"], assignment_name=name, **kwargs)

        with FILE_MANAGER.open("autograder/results/results.json") as f:
            actual_results = json.load(f)

        assert (
            actual_results == expected_results
        ), f"Actual results did not matched expected:\n{actual_results}"

    error_message_template = (
        "Received submission for assignment '{got}' (this is assignment " "'{want}')"
    )

    try:
        # test with correct name
        nb["metadata"]["otter"] = {"assignment_name": name}
        perform_test(nb, expected_results)

        # test with wrong name
        bad_name = "lab01"
        error_message = error_message_template.format(got=bad_name, want=name)
        nb["metadata"]["otter"]["assignment_name"] = bad_name
        perform_test(nb, get_expected_error_results(error_message), error=error_message)

        # test with no name in nb
        error_message = error_message_template.format(got=None, want=name)
        nb["metadata"]["otter"].pop("assignment_name")
        perform_test(nb, get_expected_error_results(error_message), error=error_message)

    finally:
        delete_paths([nb_path])
        with open(nb_path, "w+") as f:
            nbformat.write(orig_nb, f)


def test_rmd(load_config, expected_rmd_results):
    name = "hw01"
    config = load_config(True)
    rmd_path = FILE_MANAGER.get_path("rmd-autograder/submission/hw01.Rmd")
    with open(rmd_path) as f:
        orig_rmd = f.read()

    sub_name = lambda n: re.sub(r"assignment_name: \"\w+\"", f'assignment_name: "{n}"', orig_rmd)

    def perform_test(rmd, expected_results, error=None, **kwargs):
        with open(rmd_path, "w") as f:
            f.write(rmd)

        cm = (
            pytest.raises(OtterRuntimeError, match=re.escape(error))
            if error is not None
            else nullcontext()
        )
        with cm:
            run_autograder(config["autograder_dir"], assignment_name=name, **kwargs)

        with FILE_MANAGER.open("rmd-autograder/results/results.json") as f:
            actual_results = json.load(f)

        # print(actual_results["tests"][1]["output"])

        assert (
            actual_results == expected_results
        ), f"Actual results did not matched expected:\n{actual_results}"

    error_message_template = (
        "Received submission for assignment '{got}' (this is assignment " "'{want}')"
    )

    try:
        # test with correct name
        perform_test(orig_rmd, expected_rmd_results)

        # test with wrong name
        bad_name = "lab01"
        error_message = error_message_template.format(got=bad_name, want=name)
        perform_test(
            sub_name(bad_name), get_expected_error_results(error_message), error=error_message
        )

        # test with no name in Rmd
        error_message = error_message_template.format(got=None, want=name)
        perform_test(
            "\n".join([l for l in orig_rmd.split("\n") if not l.startswith("assignment_name: ")]),
            get_expected_error_results(error_message),
            error=error_message,
        )

        # test that partial credit is awarded
        pc_rmd = re.sub(r"^x <- 2$", "x <- 50", orig_rmd, flags=re.MULTILINE)
        expected_results = copy.deepcopy(expected_rmd_results)
        expected_results["tests"][1]["score"] = 2
        expected_results["tests"][1]["output"] = dedent(
            """\
                q1 results:
                    q1 - 1 result:

                    q1 - 2 result:

                    q1 - 3 result:
                        `x` not equal to 2.
                        1/1 mismatches
                        [1] 50 - 2 == 48

                    q1d result:
                        as.character(x) not equal to "2".
                        1/1 mismatches
                        x[1]: "50"
                        y[1]: "2"
            """.rstrip()
        )
        perform_test(pc_rmd, expected_results)

    finally:
        delete_paths([rmd_path])
        with open(rmd_path, "w+") as f:
            f.write(orig_rmd)


@mock.patch.object(APIClient, "upload_pdf_submission")
def test_token_sanitization(mocked_upload, get_config_path, load_config, expected_results):
    """
    Tests that the PDF upload token can't be accessed by the submission.
    """
    config = load_config()
    config["token"] = "abc123"
    config.pop("plugins")

    nb = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                dedent(
                    """\
        import json
        with open("../source/otter_config.json") as f:
            config = json.load(f)
        token = config.get("token")
    """
                )
            )
        ]
    )

    tests = {
        "q1.py": dedent(
            """\
        OK_FORMAT = False

        from otter.test_files import test_case

        name = "q1"

        @test_case()
        def q1_1(env):
            assert env["token"] is None
    """
        )
    }

    expected_results = {
        "tests": [
            {
                "name": "Public Tests",
                "visibility": "visible",
                "output": "q1 results: All test cases passed!",
                "status": "passed",
            },
            {
                "name": "q1",
                "score": 1.0,
                "max_score": 1.0,
                "visibility": "hidden",
                "output": "q1 results: All test cases passed!",
            },
        ],
    }

    FILE_MANAGER.open("autograder/submission/fails2and6H.pdf", "wb+").close()

    mocked_upload.return_value.status_code = 200

    with (
        alternate_config(get_config_path(), config),
        alternate_submission(FILE_MANAGER.get_path("autograder/submission/fails2and6H.ipynb"), nb),
        alternate_tests(tests),
    ):
        run_autograder(config["autograder_dir"])

    with FILE_MANAGER.open("autograder/results/results.json") as f:
        actual_results = json.load(f)

    assert (
        actual_results == expected_results
    ), f"Actual results did not matched expected:\n{actual_results}"

    mocked_upload.assert_called()


@mock.patch.object(APIClient, "upload_pdf_submission")
def test_pdf_via_html(_, mock_export_notebook, get_config_path, load_config, expected_results):
    config = load_config()
    config["pdf_via_html"] = True
    config["token"] = "abc123"

    with alternate_config(get_config_path(), config):
        run_autograder(config["autograder_dir"])

    with FILE_MANAGER.open("autograder/results/results.json") as f:
        actual_results = json.load(f)

    assert (
        actual_results == expected_results
    ), f"Actual results did not matched expected:\n{actual_results}"
    mock_export_notebook.assert_called_with(
        "fails2and6H.ipynb",
        dest="fails2and6H.pdf",
        filtering=False,
        pagebreaks=False,
        exporter_type="html",
    )
