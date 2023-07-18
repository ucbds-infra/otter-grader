import nbformat as nbf
import pathlib
import pytest

from contextlib import nullcontext
from python_on_whales import docker
from unittest import mock

from otter import __file__ as OTTER_PATH
from otter.grade.containers import build_image

from .utils import TestFileManager


FILE_MANAGER = TestFileManager(__file__)


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


def build_image_with_local_changes(*args, **kwargs):
    """
    Build the normal Otter Grade Docker image and then overwrite it with a new one containing a
    copy of Otter with all local edits.
    """
    image = build_image(*args, **kwargs)

    docker.build(
        ".",
        build_args={"BASE_IMAGE": image},
        tags=[image],
        file=FILE_MANAGER.get_path("Dockerfile"),
        load=True,
    )

    return image


@pytest.fixture(autouse=True)
def patch_build_image():
    with mock.patch("otter.grade.containers.build_image", wraps=build_image_with_local_changes):
        yield


@pytest.fixture(autouse=True)
def patch_grading_preprocessor_add_init_and_export_cells():
    """
    A fixture that patches the ``GradingPreprocessor`` to ensure that the in the notebook being
    executed Otter is imported from the same place it is currently being imported.
    """
    from otter.execute.preprocessor import GradingPreprocessor
    orig_add_init_and_export_cells = GradingPreprocessor.add_init_and_export_cells
    
    def add_cwd_to_sys_path_cell(preprocessor, nb):
        orig_add_init_and_export_cells(preprocessor, nb)
        otter_dir = pathlib.Path(OTTER_PATH).parent.parent
        nb.cells.insert(0, nbf.v4.new_code_cell(f"import sys\nsys.path.insert(0, \"{otter_dir}\")"))

    GradingPreprocessor.add_init_and_export_cells = add_cwd_to_sys_path_cell
