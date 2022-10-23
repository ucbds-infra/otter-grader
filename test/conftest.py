import pytest


def pytest_addoption(parser):
    """
    Adds options to the pytest command used in custom fixtures.
    """
    parser.addoption(
        "--nocleanup", action="store_true", default=False, help="no cleanup")
    parser.addoption(
        "--generate-pdfs", action="store_true", default=False, 
        help="force PDF generation instead of blocking it where it is mocked")


def pytest_configure(config):
    """
    Sets pytest configuration values.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line(
        "markers", "docker: marks tests as requiring Docker (deselect with '-m \"not docker\"')")


@pytest.fixture
def cleanup_enabled(pytestconfig):
    """
    A fixture indicating whether test cleanup is enabled.
    """
    return not pytestconfig.getoption("--nocleanup")


@pytest.fixture
def pdfs_enabled(pytestconfig):
    """
    A fixture indicating whether PDFs should be generated.
    """
    return pytestconfig.getoption("--generate-pdfs")
