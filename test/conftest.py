import pathlib
import pytest

from contextlib import nullcontext
from unittest import mock


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


@pytest.fixture(autouse=True)
def disable_assign_pdf_generation(pdfs_enabled):
    """
    Disables PDF generation in Otter Assign if indicated.
    """
    if not pdfs_enabled:
        def create_fake_pdf(src, dest, **kwargs):
            if dest is None:
                dest = f"{pathlib.Path(src).stem}.pdf"

            open(dest, "wb+").close()
            return mock.DEFAULT

        cm1 = mock.patch("otter.assign.export_notebook", side_effect=create_fake_pdf)
        cm2 = mock.patch("otter.assign.knit_rmd_file", side_effect=create_fake_pdf)

    else:
        cm1, cm2 = nullcontext(), nullcontext()

    with cm1, cm2:
        yield
