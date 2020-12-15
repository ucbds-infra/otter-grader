"""
Otter Grade command-line utility. Provides local grading of submissions in parallel Docker containers.
"""

import re
import os
import pandas as pd

from .metadata import GradescopeParser, CanvasParser, JSONParser, YAMLParser
from .containers import launch_grade
from .utils import merge_csv, prune_images

def main(args):
    """Runs Otter Grade

    Args:
        args (``argparse.Namespace``): parsed command line arguments
    """
    # prune images
    if args.prune:
        if not args.force:
            sure = input("Are you sure you want to prune Otter's grading images? This action cannot be undone [y/N] ")
            sure = bool(re.match(sure, r"ye?s?", flags=re.IGNORECASE))
        else:
            sure = True
        
        if sure:
            prune_images()
        
        return

    # Asserts that exactly one metadata flag is provided
    assert sum([meta != False for meta in [
        args.gradescope,
        args.canvas,
        args.json,
        args.yaml
    ]]) <= 1, "You can specify at most one metadata flag (-g, -j, -y, -c)"

    # # Asserts that either --pdf, --tag-filter, or --html-filter but not both provided
    # assert sum([args.pdf, args.tag_filter, args.html_filter]) <= 1, "Cannot provide more than 1 PDF flag"

    # verbose flag
    verbose = args.verbose

    # Hand off metadata to parser
    if args.gradescope:
        meta_parser = GradescopeParser(args.path)
        if verbose:
            print("Found Gradescope metadata...")
    elif args.canvas:
        meta_parser = CanvasParser(args.path)
        if verbose:
            print("Found Canvas metadata...")
    elif args.json:
        meta_parser = JSONParser(os.path.join(args.json))
        if verbose:
            print("Found JSON metadata...")
    elif args.yaml:
        meta_parser = YAMLParser(os.path.join(args.yaml))
        if verbose:
            print("Found YAML metadata...")
    else:
        meta_parser = None

    # check that reqs file is valid
    # requirements = args.requirements
    # if requirements is None and os.path.isfile("requirements.txt"):
    #     requirements = "requirements.txt"
    #
    # if requirements:
    #         assert os.path.isfile(requirements), f"Requirements file {requirements} not found"

    # if not os.path.isfile(args.requirements):

    #     # if user-specified requirements not found, fail with AssertionError
    #     assert args.requirements == "requirements.txt", f"requirements file {args.requirements} does not exist"

    #     # else just set to None and reqs are ignored
    #     args.requirements = None

    if verbose:
        print("Launching docker containers...")

    #Docker
    grade_dfs = launch_grade(args.autograder,
        notebooks_dir=args.path,
        verbose=verbose,
        num_containers=args.containers,
        scripts=args.scripts,
        no_kill=args.no_kill,
        output_path=args.output_dir,
        debug=args.debug,
        zips=args.zips,
        image=args.image,
        meta_parser=meta_parser,
        pdfs=args.pdfs
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
    output_df.to_csv(os.path.join(args.output_dir, "final_grades.csv"), index=False)
