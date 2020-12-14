"""
Gradescope autograding internals
"""

import os
import json
import pandas as pd

from .constants import DEFAULT_OPTIONS
from ...version import LOGO_WITH_VERSION

def main(autograder_dir, logo=True):
    """
    Runs autograder on Gradescope based on predefined configurations.

    Args:
        config (``dict``): configurations for autograder
    """

    config_fp = os.path.join(autograder_dir, "source", "otter_config.json")
    if os.path.isfile(config_fp):
        with open(config_fp) as f:
            config = json.load(f)
    else:
        config = {}

    options = DEFAULT_OPTIONS.copy()
    options.update(config)

    if options["logo"] and logo:
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

    df = pd.DataFrame(output["tests"])
    if "output" in df.columns:
        df.drop(columns=["output"], inplace=True)

    print(df)

    os.chdir(curr_dir)
