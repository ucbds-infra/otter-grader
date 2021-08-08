"""
Otter Grade command-line utility. Provides local grading of submissions in parallel Docker containers.
"""

import click
import os
import pandas as pd
import re

from .containers import launch_grade
from .metadata import GradescopeParser, CanvasParser, JSONParser, YAMLParser
from .utils import merge_csv, prune_images

from ..cli import cli


def main(path, output_dir, autograder, gradescope, canvas, json, yaml, containers, scripts, no_kill, 
        debug, zips, image, pdfs, prune, force, verbose):
    """
    Runs Otter Grade

    Grades a directory of submissions in parallel Docker containers. Results are outputted as a CSV file
    called ``final_grades.csv``. If ``prune`` is ``True``, Otter's dangling grading images are pruned 
    and the program exits.

    Args:
        path (``str``): path to directory of submissions
        output_dir (``str``): directory in which to write ``final_grades.csv``
        autograder (``str``): path to Otter autograder configuration zip file
        gradescope (``bool``): whether submissions are a Gradescope export
        canvas (``bool``): whether submissions are a Canvas export
        json (``str``): path to a JSON metadata file
        yaml (``str``): path to a YAML metadata file
        containers (``int``): number of containers to run in parallel
        scripts (``bool``): whether Python scripts are being graded
        no_kill (``bool``): whether to keep containers after grading is finished
        debug (``bool``): whether to print the stdout of each container
        zips (``bool``): whether the submissions are Otter-exported zip files
        image (``bool``): base image from which to build grading image
        pdfs (``bool``): whether to copy notebook PDFs out of the containers
        prune (``bool``): whether to prune dangling grading images
        force (``bool``): whether to force pruning (without confirmation)
        verbose (``bool``): whether to log status messages to stdout
        **kwargs: ignored kwargs (a remnant of how the argument parser is built)

    Raises:
        ``AssertionError``: if invalid arguments are provided
    """
    # prune images
    if prune:
        if not force:
            sure = input("Are you sure you want to prune Otter's grading images? This action cannot be undone [y/N] ")
            sure = bool(re.match(sure, r"ye?s?", flags=re.IGNORECASE))
        else:
            sure = True
        
        if sure:
            prune_images()
        
        return

    # Asserts that exactly one metadata flag is provided
    assert sum([meta != False for meta in [
        gradescope,
        canvas,
        json,
        yaml
    ]]) <= 1, "You can specify at most one metadata flag (-g, -j, -y, -c)"

    # verbose flag
    verbose = verbose

    # Hand off metadata to parser
    if gradescope:
        meta_parser = GradescopeParser(path)
        if verbose:
            print("Found Gradescope metadata...")
    elif canvas:
        meta_parser = CanvasParser(path)
        if verbose:
            print("Found Canvas metadata...")
    elif json:
        meta_parser = JSONParser(os.path.join(json))
        if verbose:
            print("Found JSON metadata...")
    elif yaml:
        meta_parser = YAMLParser(os.path.join(yaml))
        if verbose:
            print("Found YAML metadata...")
    else:
        meta_parser = None

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
        meta_parser=meta_parser,
        pdfs=pdfs
    )

    if verbose:
        print("Combining grades and saving...")

    # Merge Dataframes
    output_df = merge_csv(grade_dfs)

    def map_files_to_ids(row):
        """Returns the identifier for the filename in the specified row"""
        return meta_parser.file_to_id(row["file"])

    # add in identifier column
    if meta_parser is not None:
        output_df["identifier"] = output_df.apply(map_files_to_ids, axis=1)
        output_df.drop("file", axis=1, inplace=True)

        # reorder cols in output_df
        cols = output_df.columns.tolist()
        output_df = output_df[cols[-1:] + cols[:-1]]

    # write to CSV file
    output_df.to_csv(os.path.join(output_dir, "final_grades.csv"), index=False)


@cli.command("grade")

# necessary path arguments
@click.option("-p", "--path", default="./", type=click.Path(exists=True, file_okay=False), help="Path to directory of submissions")
@click.option("-a", "--autograder", default="./autograder.zip", type=click.Path(exists=True, dir_okay=False), help="Path to autograder zip file")
@click.option("-o", "--output-dir", default="./", type=click.Path(exists=True, file_okay=False), help="Directory to which to write output")

# metadata parser arguments
@click.option("-g", "--gradescope", is_flag=True, help="Flag for Gradescope export")
@click.option("-c", "--canvas", is_flag=True, help="Flag for Canvas export")
@click.option("-j", "--json", default=False, type=click.Path(exists=True, dir_okay=False), help="Flag for path to JSON metadata")
@click.option("-y", "--yaml", default=False, type=click.Path(exists=True, dir_okay=False), help="Flag for path to YAML metadata")

# submission format arguments
@click.option("-s", "--scripts", is_flag=True, help="Flag to incidicate grading Python scripts")
@click.option("-z", "--zips", is_flag=True, help="Whether submissions are zip files from Notebook.export")

# PDF export options
@click.option("--pdfs", is_flag=True, help="Whether to copy notebook PDFs out of containers")

# other settings and optional arguments
@click.option("-v", "--verbose", is_flag=True, help="Flag for verbose output")
@click.option("--containers", type=click.INT, help="Specify number of containers to run in parallel")
@click.option("--image", default="ucbdsinfra/otter-grader", help="Custom docker image to run on")
@click.option("--no-kill", is_flag=True, help="Do not kill containers after grading")
@click.option("--debug", is_flag=True, help="Print stdout/stderr from grading for debugging")

@click.option("--prune", is_flag=True, help="Prune all of Otter's grading images")
@click.option("-f", "--force", is_flag=True, help="Force action (don't ask for confirmation)")
def grade_cli(*args, **kwargs):
    return main(*args, **kwargs)
