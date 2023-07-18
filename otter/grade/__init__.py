"""Local grading of submissions in Docker containers for Otter-Grader"""

import os
import re

from glob import glob
from typing import List, Optional, Tuple, Union

from .containers import launch_containers
from .utils import merge_csv, prune_images

from ..run.run_autograder.autograder_config import AutograderConfig
from ..utils import assert_path_exists, loggers


_ALLOWED_EXTENSIONS = ["ipynb", "py", "Rmd", "R", "r", "zip"]
LOGGER = loggers.get_logger(__name__)


def main(
    *,
    name: Optional[str] = None,
    paths: Optional[Union[List[str], Tuple[str]]] = None,
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
    debug: bool = False,
):
    """
    Run Otter Grade.

    Grades a directory of submissions in parallel Docker containers. Results are written as a CSV
    file called ``final_grades.csv`` in ``output_dir``. If ``pdfs`` is true, the PDFs generated
    inside the Docker containers are copied into a subdirectory of ``output_dir`` called
    ``submission_pdfs``.

    If ``prune`` is true, Otter's dangling grading images are pruned and the program exits.

    Args:
        name (``str``): an assignment name to use in the Docker image tag; must be specified unless
            ``prune`` is true
        paths (``list[str] | tuple[str]``): paths to submission files or directories of submissions
            for grading
        output_dir (``str``): path to directory where output should be written
        autograder (``str``): path to an Otter autograder configuration zip file
        containers (``int``): number of containers to run in parallel
        ext (``str``): the submission file extension (to be used in a glob pattern)
        no_kill (``bool``): whether to keep containers after grading is finished
        image (``str``): a Docker image to use as the base image for the grading image
        pdfs (``bool``): whether to copy notebook PDFs out of the containers
        prune (``bool``): whether to prune the grading images; if true, no grading is performed
        force (``bool``): whether to force-prune the images (do not ask for confirmation)
        timeout (``int``): an execution timeout in seconds for each container
        no_network (``bool``): whether to disable networking in the containers
        debug (``bool``): whether to run autograding in debug mode

    Returns:
        ``float | None``: the percentage scored by that submission if a single file was graded
            otherwise ``None``

    Raises:
        ``FileNotFoundError``: if a provided directory or file doesn't exist
        ``ValueError``: if an unsupported extension is passed to ``ext``
    """
    if prune:
        prune_images(force=force)
        return

    if name is None:
        raise ValueError("You must specify an assignment name")
    elif not re.match(r"^[\w\-.]+$", name):
        raise ValueError("Assignment names may only contain letters, nubers, underscores, dashes, and periods")

    if not isinstance(paths, tuple) and not isinstance(paths, list):
        raise TypeError("paths must be a tuple of valid paths")
    elif len(paths) == 0:
        raise ValueError("No paths specified")

    # check file paths
    assert_path_exists([
        (output_dir, True),
        (autograder, False),
    ])

    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid submission extension specified: {ext}")

    LOGGER.info("Launching Docker containers")

    pattern = f"*.{ext}"
    submission_paths = []
    for path in paths:
        if os.path.isdir(path):
            submission_paths.extend(glob(os.path.join(path, pattern)))
        else:
            submission_paths.append(path)

    LOGGER.debug(f"Resolved submission paths: {submission_paths}")

    pdf_dir = os.path.join(output_dir, "submission_pdfs") if pdfs else None

    grade_dfs = launch_containers(
        autograder,
        submission_paths,
        num_containers = containers,
        base_image = image,
        tag = name,
        no_kill = no_kill,
        pdf_dir = pdf_dir,
        timeout = timeout,
        network = not no_network,
        config = AutograderConfig({
            "zips": ext == "zip",
            "pdf": pdfs,
            "debug": debug,
        }),
    )

    LOGGER.info("Combining grades and saving")

    # Merge dataframes
    output_df = merge_csv(grade_dfs)
    cols = output_df.columns.tolist()
    output_df = output_df[cols[-1:] + cols[:-1]]

    # write to CSV file
    output_df.to_csv(os.path.join(output_dir, "final_grades.csv"), index=False)

    # return percentage if a single file was graded
    if len(paths) == 1 and os.path.isfile(paths[0]):
        return output_df["percent_correct"][0]
