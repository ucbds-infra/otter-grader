"""Local grading of submissions in Docker containers for Otter-Grader"""

import os
import pandas as pd
import re

from .containers import launch_grade
from .utils import merge_csv, prune_images

from ..utils import assert_path_exists


def main(*, path="./", output_dir="./", autograder="./autograder.zip", containers=None, 
         scripts=False, no_kill=False, debug=False, zips=False, image="ucbdsinfra/otter-grader", 
         pdfs=False, verbose=False, prune=False, force=False):
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
        scripts (``bool``): whether Python scripts are being graded
        no_kill (``bool``): whether to keep containers after grading is finished
        debug (``bool``): whether to print the stdout of each container
        zips (``bool``): whether the submissions are Otter-exported zip files
        image (``bool``): base image from which to build grading image
        pdfs (``bool``): whether to copy notebook PDFs out of the containers
        verbose (``bool``): whether to log status messages to stdout
        prune (``bool``): whether to prune the grading images; if true, no grading is performed
        force (``bool``): whether to force-prune the images (do not ask for confirmation)

    Raises:
        ``AssertionError``: if invalid arguments are provided
    """
    if prune:
        prune_images(force=force)
        return

    # check file paths
    assert_path_exists([
        (path, True),
        (output_dir, True),
        (autograder, False),
    ])

    if verbose:
        print("Launching docker containers...")

    #Docker
    grade_dfs = launch_grade(autograder,
        notebooks_dir=path,
        verbose=verbose,
        num_containers=containers,
        scripts=scripts,
        no_kill=no_kill,
        output_path=output_dir,
        debug=debug,
        zips=zips,
        image=image,
        pdfs=pdfs
    )

    if verbose:
        print("Combining grades and saving...")

    # Merge Dataframes
    output_df = merge_csv(grade_dfs)
    cols = output_df.columns.tolist()
    output_df = output_df[cols[-1:] + cols[:-1]]

    # write to CSV file
    output_df.to_csv(os.path.join(output_dir, "final_grades.csv"), index=False)
