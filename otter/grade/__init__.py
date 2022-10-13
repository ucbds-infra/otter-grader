"""Local grading of submissions in Docker containers for Otter-Grader"""

import os
import shutil
import tempfile

from .containers import launch_containers
from .utils import merge_csv, prune_images

from ..utils import assert_path_exists, loggers


_ALLOWED_EXTENSIONS = ["ipynb", "py", "Rmd", "R", "r", "zip"]
LOGGER = loggers.get_logger(__name__)


def main(
    *,
    path: str = "./",
    output_dir: str = "./",
    autograder: str = "./autograder.zip",
    containers: int = 4, 
    ext: str = "ipynb",
    no_kill: bool = False,
    image: str = "ubuntu:22.04", 
    pdfs: bool = False,
    prune: bool = False,
    force: bool = False,
    timeout: bool = None,
    no_network: bool = False,
):
    """
    Run Otter Grade.

    Grades a directory of submissions in parallel Docker containers. Results are written as a CSV
    file called ``final_grades.csv`` in ``output_dir``. If ``pdfs`` is true, the PDFs generated
    inside the Docker containers are copied into a subdirectory of ``output_dir`` called
    ``submission_pdfs``.
    
    If ``prune`` is true, Otter's dangling grading images are pruned and the program exits.

    Args:
        path (``str``): path to directory of submissions
        output_dir (``str``): path to directory where output should be written
        autograder (``str``): path to an Otter autograder configuration zip file
        containers (``int``): number of containers to run in parallel
        ext (``str``): the submission file extension (to be used in a glob pattern)
        no_kill (``bool``): whether to keep containers after grading is finished
        image (``str``): a Docker image tag to use as the base image for the grading image
        pdfs (``bool``): whether to copy notebook PDFs out of the containers
        prune (``bool``): whether to prune the grading images; if true, no grading is performed
        force (``bool``): whether to force-prune the images (do not ask for confirmation)
        timeout (``int``): an execution timeout in seconds for each container
        no_network (``bool``): whether to disable networking in the containers

    Raises:
        ``FileNotFoundError``: if a provided directory or file doesn't exist
        ``ValueError``: if an unsupported extension is passed to ``ext``
    """
    if prune:
        prune_images(force=force)
        return

    # if path leads to single file this indicates the case and changes path to the directory and
    # updates the ext argument
    single_file = False
    if os.path.isfile(path):
        single_file = True
        ext = os.path.splitext(path)[1][1:]  # remove the period from extension
        file = os.path.split(path)[1]
        temp_dir = tempfile.mkdtemp(prefix="otter_")
        temp_file_path = os.path.join(temp_dir, file)
        shutil.copy(path, temp_file_path)
        path = temp_dir

    # check file paths
    assert_path_exists([
        (path, True),
        (output_dir, True),
        (autograder, False),
    ])

    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid submission extension specified: {ext}")

    LOGGER.info("Launching Docker containers")

    grade_dfs = launch_containers(
        autograder,
        submissions_dir=path,
        num_containers=containers,
        ext=ext,
        no_kill=no_kill,
        output_path=output_dir,
        image=image,
        pdfs=pdfs,
        timeout=timeout,
        network=not no_network,
    )

    LOGGER.info("Combining grades and saving")

    # Merge dataframes
    output_df = merge_csv(grade_dfs)
    cols = output_df.columns.tolist()
    output_df = output_df[cols[-1:] + cols[:-1]]

    # write to CSV file
    output_df.to_csv(os.path.join(output_dir, "final_grades.csv"), index=False)
    if single_file:
        shutil.rmtree(temp_dir)
        return output_df["percent_correct"][0]
