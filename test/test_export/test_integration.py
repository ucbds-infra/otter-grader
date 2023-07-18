"""Tests for ``otter.export``"""

# NOTES:
# - tests do not check for PDF equality

import filecmp
import nbconvert
import nbformat
import os
import pytest

from glob import glob
from unittest import mock

from otter.export import main as export
from otter.export.exporters.base_exporter import BaseExporter
from otter.utils import nullcontext

from ..utils import TestFileManager


FILE_MANAGER = TestFileManager(__file__)


@pytest.fixture(autouse=True)
def cleanup_output(cleanup_enabled):
    """
    Removes export output
    """
    yield
    if cleanup_enabled:
        for file in glob(FILE_MANAGER.get_path("*.pdf")) + glob(FILE_MANAGER.get_path("*.tex")) + \
                [FILE_MANAGER.get_path("output.ipynb")]:
            if os.path.exists(file):
                os.remove(file)


@pytest.fixture(autouse=True)
def disable_pdf_generation(pdfs_enabled):
    if not pdfs_enabled:
        def create_fake_pdf(exporter, nb):
            contents = "pdf contents"
            if isinstance(exporter, nbconvert.PDFExporter):
                contents = contents.encode("utf-8")
            return contents, {}

        cm = mock.patch("otter.export.exporters.via_html.nbconvert.export", side_effect=create_fake_pdf)
        cm2 = mock.patch("otter.export.exporters.via_latex.nbconvert.export", side_effect=create_fake_pdf)

    else:
        cm, cm2 = nullcontext(), nullcontext()

    with cm, cm2:
        yield


def run_export(notebook_path, **kwargs):
    export(notebook_path, **kwargs)


def test_success_HTML():
    """
    Tests a successful export with filtering and no pagebreaks
    """
    test_file = "successful-html-test"
    run_export(
        FILE_MANAGER.get_path(f"{test_file}.ipynb"), filtering=True, save=True, exporter="latex")

    # check existence of pdf and tex
    FILE_MANAGER.assert_path_exists(FILE_MANAGER.get_path(f"{test_file}.pdf"), dir_okay=False)
    FILE_MANAGER.assert_path_exists(FILE_MANAGER.get_path(f"{test_file}.tex"), dir_okay=False)


def test_success_pagebreak():
    """
    Tests a successful filter with pagebreaks
    """
    test_file = "success-pagebreak-test"
    run_export(
        FILE_MANAGER.get_path(f"{test_file}.ipynb"), 
        filtering=True, 
        exporter="latex", 
        pagebreaks=True, 
        save=True,
    )

    # check existence of pdf and tex
    FILE_MANAGER.assert_path_exists(FILE_MANAGER.get_path(f"{test_file}.pdf"), dir_okay=False)
    FILE_MANAGER.assert_path_exists(FILE_MANAGER.get_path(f"{test_file}.tex"), dir_okay=False)


def test_no_close():
    """
    Tests a filtered export without a closing comment
    """
    test_file = "no-close-tag-test"
    run_export(
        FILE_MANAGER.get_path(f"{test_file}.ipynb"), 
        filtering=True, 
        exporter="latex", 
        pagebreaks=True, 
        save=True,
    )

    # check existence of pdf and tex
    FILE_MANAGER.assert_path_exists(FILE_MANAGER.get_path(f"{test_file}.pdf"), dir_okay=False)
    FILE_MANAGER.assert_path_exists(FILE_MANAGER.get_path(f"{test_file}.tex"), dir_okay=False)


def test_load_notebook():
    """
    Tests a successful load_notebook
    """
    test_file = "successful-html-test"
    node = BaseExporter.load_notebook(FILE_MANAGER.get_path(f"{test_file}.ipynb"), filtering=True)

    nbformat.write(node, FILE_MANAGER.get_path("output.ipynb"))

    # check file contents
    assert filecmp.cmp(FILE_MANAGER.get_path("output.ipynb"), FILE_MANAGER.get_path(f"correct/{test_file}.ipynb"))
