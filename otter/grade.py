###################################################
##### Command Line Interface for Otter-Grader #####
###################################################

import os
import pandas as pd

from .metadata import *
from .containers import *
from .utils import *

def main(args):
    """
    Main function for running otter from the command line.
    """
    # Asserts that exactly one metadata flag is provided
    assert sum([meta != False for meta in [
        args.gradescope, 
        args.canvas, 
        args.json, 
        args.yaml
    ]]) == 1, "You must supply exactly one metadata flag (-g, -j, -y, -c)"

    # Asserts that either --pdf, --tag-filter, or --html-filter but not both provided
    assert sum([args.pdf, args.tag_filter, args.html_filter]) <= 1, "Cannot provide more than 1 PDF flag"

    # verbose flag
    verbose = args.verbose

    # Hand off metadata to parser
    if args.gradescope:
        meta_parser = GradescopeParser(args.notebooks_path)
        if verbose:
            print("Found Gradescope metadata...")
    elif args.canvas:
        meta_parser = CanvasParser(args.notebooks_path)
        if verbose:
            print("Found Canvas metadata...")
    elif args.json:
        meta_parser = JSONParser(os.path.join(args.json))
        if verbose:
            print("Found JSON metadata...")
    else:
        meta_parser = YAMLParser(os.path.join(args.yaml))
        if verbose:
            print("Found YAML metadata...")

    # check that reqs file is valid
    if not (os.path.exists(args.requirements) and os.path.isfile(args.requirements)):
        
        # if user-specified requirements not found, fail with AssertionError
        if args.requirements != "requirements.txt":
            assert False, "requirements file {} does not exist".format(args.requirements)

        # else just set to None and reqs are ignored
        args.requirements = None

    if verbose:
        print("Launching docker containers...")

    # Docker
    grades_dfs = launch_parallel_containers(args.tests_path, 
        args.notebooks_path, 
        verbose=verbose, 
        unfiltered_pdfs=args.pdf, 
        tag_filter=args.tag_filter,
        html_filter=args.html_filter,
        reqs=args.requirements,
        num_containers=args.num_containers,
        image=args.image,
        scripts=args.scripts,
        no_kill=args.no_kill
    )

    if verbose:
        print("Combining grades and saving...")

    # Merge Dataframes
    output_df = merge_csv(grades_dfs)

    def map_files_to_ids(row):
        """Returns the identifier for the filename in the specified row"""
        return meta_parser.file_to_id(row["file"])

    # add in identifier column
    output_df["identifier"] = output_df.apply(map_files_to_ids, axis=1)

    # reorder cols in output_df
    cols = output_df.columns.tolist()
    output_df = output_df[cols[-1:] + cols[:-1]]

    # write to CSV file
    output_df.to_csv(os.path.join(args.output_path, "final_grades.csv"), index=False)

if __name__ == "__main__":
    main()
