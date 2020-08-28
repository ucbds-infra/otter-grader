"""
Gradescope autograding internals
"""

import os
import json
import pandas as pd

from ...version import LOGO_WITH_VERSION

def main(config):
    """
    Runs autograder on Gradescope based on predefined configurations.

    Args:
        config (``dict``): configurations for autograder
    """
    print(LOGO_WITH_VERSION, "\n")

    curr_dir = os.getcwd()

    if "lang" in config and config["lang"].lower() == "r":
        from .r_adapter.run_autograder import run_autograder
    
    else:
        from .run_autograder import run_autograder
    
    output = run_autograder(config)

    with open("./results/results.json", "w+") as f:
        json.dump(output, f, indent=4)

    print("\n\n")

    df = pd.DataFrame(output["tests"])
    if "output" in df.columns:
        df.drop(columns=["output"], inplace=True)

    print(df)

    os.chdir(curr_dir)
