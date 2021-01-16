"""
Gradescope autograding internals
"""

import os
import json
import pandas as pd

from .constants import DEFAULT_OPTIONS
from ...version import LOGO_WITH_VERSION

def main(autograder_dir, **kwargs):
    """
    Runs autograder based on predefined configurations

    Args:
        autograder_dir (``str``): the absolute path of the directory in which autograding is occurring
            (e.g. on Gradescope, this is ``/autograder``)
        **kwargs: keyword arguments for updating configurations in the default configurations 
            ``otter.run.run_autograder.constants.DEFAULT_OPTIONS``; these values override anything
            present in ``otter_config.json``
    """

    config_fp = os.path.join(autograder_dir, "source", "otter_config.json")
    if os.path.isfile(config_fp):
        with open(config_fp) as f:
            config = json.load(f)
    else:
        config = {}

    options = DEFAULT_OPTIONS.copy()
    options.update(config)
    options.update(kwargs)

    if options["logo"]:
        print(LOGO_WITH_VERSION, "\n")

    options["autograder_dir"] = autograder_dir

    curr_dir = os.getcwd()

    if options["lang"].lower() == "r":
        from .r_adapter.run_autograder import run_autograder
    
    else:
        from .run_autograder import run_autograder
    
    output = run_autograder(options)

    with open("./results/results.json", "w+") as f:
        json.dump(output, f, indent=4)

    print("\n\n")

    if options["print_summary"]:
        df = pd.DataFrame(output["tests"])
        if "output" in df.columns:
            df.drop(columns=["output"], inplace=True)

        print(df)

    os.chdir(curr_dir)
