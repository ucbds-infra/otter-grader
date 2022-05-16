"""Local grading of submissions in Docker containers for Otter-Grader"""

import os
import pandas as pd
import re
import shutil
import tempfile

from .containers import launch_grade
from .utils import merge_csv, prune_images

from ..utils import assert_path_exists, loggers


_ALLOWED_EXTENSIONS = ["ipynb", "py", "Rmd", "R", "r"]
LOGGER = loggers.get_logger(__name__)


def main(*, path="./", output_dir="./", autograder="./autograder.zip", containers=None, 
         ext="ipynb", no_kill=False, debug=False, zips=False, image="ucbdsinfra/otter-grader", 
         pdfs=False, verbose=False, prune=False, force=False, timeout=None, no_network=False):
    """
    Runs Otter Grade

    Grades a directory of submissions in parallel Docker containers. Results are outputted as a CSV file
    called ``final_grades.csv``. If ``prune`` is ``True``, Otter's dangling grading images are pruned 
    and the program exits.

    Args:
        path (``str``): path to directory of submissions
        output_dir (``str``): directory in which to write ``final_grades.csv``
        autograder (``str``): path to Otter autograder configuration zip file
        containers (``int``): number of containers to run in parallel
        ext (``str``): the submission file extension for globbing
        no_kill (``bool``): whether to keep containers after grading is finished
        zips (``bool``): whether the submissions are Otter-exported zip files
        image (``str``): base image from which to build grading image
        pdfs (``bool``): whether to copy notebook PDFs out of the containers
        prune (``bool``): whether to prune the grading images; if true, no grading is performed
        force (``bool``): whether to force-prune the images (do not ask for confirmation)
        timeout (``int``): timeout in seconds for each container
        no_network (``bool``): whether to disable networking in the containers

    Raises:
        ``AssertionError``: if invalid arguments are provided
    """
    if prune:
        prune_images(force=force)
        return

    # if path leads to single file this indicates
    # the case and changes path to the directory
    # as well as updates the ext argument
    single_file = False
    temp_file_path = ""
    if os.path.isfile(path):
        single_file = True
        ext = os.path.splitext(path)[1][1:]  # remove the period from extension
        file = os.path.split(path)[1]
        temp_dir = tempfile.mkdtemp(prefix="otter_")
        temp_file_path = f"{temp_dir}/{file}"
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

    #Docker
    grade_dfs = launch_grade(autograder,
        submissions_dir=path,
        num_containers=containers,
        ext=ext,
        no_kill=no_kill,
        output_path=output_dir,
        zips=zips,
        image=image,
        pdfs=pdfs,
        timeout=timeout,
        network=not no_network,
    )

    LOGGER.info("Combining grades and saving")

    # Merge Dataframes
    output_df = merge_csv(grade_dfs)
    cols = output_df.columns.tolist()
    output_df = output_df[cols[-1:] + cols[:-1]]

    # write to CSV file
    output_df.to_csv(os.path.join(output_dir, "final_grades.csv"), index=False)
    if single_file:
        shutil.rmtree(temp_dir)
        return output_df["percent_correct"][0]
