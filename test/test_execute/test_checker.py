import pytest

from unittest.mock import patch, MagicMock

from otter.execute.checker import Checker
from otter.test_files import OKTestFile


@pytest.fixture
def mocked_create_test_file():
    with patch("otter.execute.checker.create_test_file") as m:
        yield m


@pytest.fixture(autouse=True)
def reset_checker():
    Checker.clear_results()
    Checker.disable_tracking()


class TestChecker:
    """
    Tests for ``otter.execute.checker.Checker``.
    """

    def test_tracking_disabled(self, mocked_create_test_file):
        res = Checker.get_results()
        Checker.check("")
        assert len(res) == 0

    def test_tracking_enabled(self, mocked_create_test_file):
        res = Checker.get_results()
        Checker.enable_tracking()
        Checker.check("")
        assert len(res) == 1

    def test_tracking_toggles(self, mocked_create_test_file):
        res = Checker.get_results()
        Checker.check("")
        assert len(res) == 0

        Checker.enable_tracking()
        Checker.check("")
        assert len(res) == 1

        Checker.check("")
        assert len(res) == 2

        Checker.disable_tracking()
        Checker.check("")
        assert len(res) == 2

    def test_get_results_and_clear_results(self, mocked_create_test_file):
        res = Checker.get_results()
        assert res is Checker.get_results()

        Checker.clear_results()
        assert res is not Checker.get_results()

    @patch("otter.execute.checker.inspect.currentframe")
    def test_check_path_only(self, mocked_currentframe, mocked_create_test_file):
        path = "foo.ipynb"

        ret = Checker.check(path)

        mocked_create_test_file.assert_called_once_with(path, test_name=None)
        mocked_currentframe.assert_called_once()
        mocked_create_test_file.return_value.run.assert_called_once_with(
            mocked_currentframe.return_value.f_back.f_globals)
        assert ret is mocked_create_test_file.return_value

    @patch("otter.execute.checker.inspect.currentframe")
    def test_check_path_and_test_name(self, mocked_currentframe, mocked_create_test_file):
        path, test_name = "foo.ipynb", "q1"

        ret = Checker.check(path, test_name)

        mocked_create_test_file.assert_called_once_with(path, test_name=test_name)
        mocked_currentframe.assert_called_once()
        mocked_create_test_file.return_value.run.assert_called_once_with(
            mocked_currentframe.return_value.f_back.f_globals)
        assert ret is mocked_create_test_file.return_value

    @patch("otter.execute.checker.inspect.currentframe")
    def test_check_path_and_global_env(self, mocked_currentframe, mocked_create_test_file):
        path, global_env = "foo.ipynb", {}

        ret = Checker.check(path, global_env=global_env)

        mocked_create_test_file.assert_called_once_with(path, test_name=None)
        mocked_currentframe.assert_not_called()
        mocked_create_test_file.return_value.run.assert_called_once_with(global_env)
        assert ret is mocked_create_test_file.return_value

    @patch("otter.execute.checker.inspect.currentframe")
    @patch.object(Checker, "check")
    def test_check_if_not_already_checked(self, mocked_check, mocked_currentframe):
        Checker._test_files = [
            OKTestFile("", "q1.py", []),
            OKTestFile("", "tests/q2.py", []),
            OKTestFile("", "/path/to/tests/q3.py", []),
        ]

        for t in [
            {"path": "q1.py", "want_call": False},
            {"path": "q2.py", "want_call": False},
            {"path": "q3.py", "want_call": False},
            {"path": "/path/to/tests/q2.py", "want_call": False},
            {"path": "tests/q3.py", "want_call": False},
            {"path": "q4.py", "want_call": True},
            {"path": "tests/q4.py", "want_call": True},
            {"path": "/path/to/tests/q4.py", "want_call": True},
        ]:
            mocked_check.reset_mock()

            ret = Checker.check_if_not_already_checked(t["path"], t.get("global_env"))

            if t["want_call"]:
                global_env = t.get("global_env", mocked_currentframe.return_value.f_back.f_globals)
                mocked_check.assert_called_once_with(t["path"], global_env=global_env)
                assert ret is mocked_check.return_value
            else:
                mocked_check.assert_not_called()
