import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--nocleanup", action="store_true", default=False, help="no cleanup")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line(
        "markers", "docker: marks tests as requiring Docker (deselect with '-m \"not docker\"')")


@pytest.fixture
def cleanup_enabled(pytestconfig):
    return not pytestconfig.getoption("--nocleanup")
