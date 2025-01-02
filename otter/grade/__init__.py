"""Local grading of submissions in Docker containers for Otter-Grader"""

import os
import pathlib
import re

from glob import glob
from multiprocessing import Queue
from typing import Optional, Union

from .containers import launch_containers
from .utils import merge_scores_to_df, prune_images, SCORES_DICT_PERCENT_CORRECT_KEY
from .. import logging
from ..run import AutograderConfig
from ..utils import assert_path_exists


ALLOWED_EXTENSIONS = ["ipynb", "py", "Rmd", "R", "r", "zip"]
LOGGER = logging.get_logger(__name__)


def main(
    *,
    name: Optional[str] = None,
    paths: Optional[Union[list[str], tuple[str]]] = None,
    output_dir: str = "./",
    autograder: str = "./autograder.zip",
    containers: int = 4,
    ext: str = "ipynb",
    summaries: bool = False,
    no_kill: bool = False,
    image: str = "ubuntu:22.04",
    pdfs: bool = False,
    prune: bool = False,
    force: bool = False,
    timeout: Optional[int] = None,
    no_network: bool = False,
    debug: bool = False,
    result_queue: Optional["Queue[str]"] = None,
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
        timeout (``int | None``): an execution timeout in seconds for each container
        no_network (``bool``): whether to disable networking in the containers
        debug (``bool``): whether to run autograding in debug mode
        result_queue (``multiprocessing.Queue[str] | None``): the queue to store progress messages

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
        raise ValueError(
            "Assignment names may only contain letters, numbers, underscores, dashes, and periods"
        )

    if not isinstance(paths, tuple) and not isinstance(paths, list):
        raise TypeError("paths must be a tuple of valid paths")
    elif len(paths) == 0:
        raise ValueError("No paths specified")

    # check file paths
    assert_path_exists(
        [
            (output_dir, True),
            (autograder, False),
        ]
    )

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid submission extension specified: {ext}")

    out = pathlib.Path(output_dir)
    try:
        if result_queue:
            logging.add_queue_handler(result_queue)

        LOGGER.info("Launching Docker containers")

        pattern = f"*.{ext}"
        submission_paths = []
        for path in paths:
            if os.path.isdir(path):
                submission_paths.extend(glob(os.path.join(path, pattern)))
            else:
                submission_paths.append(path)

        LOGGER.debug(f"Resolved submission paths: {submission_paths}")

        pdf_dir = out / "submission_pdfs" if pdfs else None

        scores = launch_containers(
            autograder,
            submission_paths,
            num_containers=containers,
            base_image=image,
            tag=name,
            no_kill=no_kill,
            pdf_dir=pdf_dir,
            timeout=timeout,
            network=not no_network,
            config=AutograderConfig(
                {
                    "zips": ext == "zip",
                    "pdf": pdfs,
                    "debug": debug,
                }
            ),
        )

        LOGGER.info("Combining grades and saving")
    finally:
        logging.remove_queue_handlers()

    # Merge scores to dataframe
    output_df = merge_scores_to_df(scores)

    # write to CSV file
    output_df.to_csv(out / "final_grades.csv", index=False)

    # write score summaries to files
    if summaries:
        grading_summary_path = out / "grading-summaries"
        if not grading_summary_path.exists():
            grading_summary_path.mkdir()

        for s in scores:
            nb_name, _ = os.path.splitext(s.file)
            with open(grading_summary_path / f"{nb_name}.txt", mode="w") as f:
                f.write(s.summary())

    # return percentage if a single file was graded
    if len(paths) == 1 and os.path.isfile(paths[0]):
        return output_df[SCORES_DICT_PERCENT_CORRECT_KEY][1]
