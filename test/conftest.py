import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--nocleanup", action="store_true", default=False, help="no cleanup")


@pytest.fixture
def cleanup_enabled(pytestconfig):
    return not pytestconfig.getoption("--nocleanup")
