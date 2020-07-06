##########################################
##### Local Grading for Otter-Grader #####
##########################################

import os
import pandas as pd

from .metadata import GradescopeParser, CanvasParser, JSONParser, YAMLParser
from .containers import launch_parallel_containers
from .utils import merge_csv

def main(args):
    """Runs Otter Grade

    Args:
        args (``argparse.Namespace``): parsed command line arguments
    """
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
    if not os.path.isfile(args.requirements):
        
        # if user-specified requirements not found, fail with AssertionError
        assert args.requirements == "requirements.txt", f"requirements file {args.requirements} does not exist"

        # else just set to None and reqs are ignored
        args.requirements = None

    if verbose:
        print("Launching docker containers...")

    # Docker
    grades_dfs = launch_parallel_containers(args.tests_path, 
        args.path, 
        verbose=verbose, 
        pdfs=args.pdfs,
        # unfiltered_pdfs=args.pdf, 
        # tag_filter=args.tag_filter,
        # html_filter=args.html_filter,
        reqs=args.requirements,
        num_containers=args.containers,
        image=args.image,
        scripts=args.scripts,
        no_kill=args.no_kill,
        output_path=args.output_path,
        debug=args.debug,
        seed=args.seed,
        zips=args.zips,
        meta_parser=meta_parser
    )

    if verbose:
        print("Combining grades and saving...")

    # Merge Dataframes
    output_df = merge_csv(grades_dfs)

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
    output_df.to_csv(os.path.join(args.output_path, "final_grades.csv"), index=False)
