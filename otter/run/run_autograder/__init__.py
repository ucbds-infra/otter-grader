"""Autograding process internals for Otter-Grader"""

import os
import json
import pandas as pd
import pickle

from .runners import create_runner
from .utils import OtterRuntimeError
from ...version import LOGO_WITH_VERSION
from ...utils import chdir


def main(autograder_dir, **kwargs):
    """
    Run the autograding process.

    Args:
        autograder_dir (``str``): the absolute path of the directory in which autograding is occurring
            (e.g. on Gradescope, this is ``/autograder``)
        **kwargs: keyword arguments for updating configurations in the default configurations 
            ``otter.run.run_autograder.constants.DEFAULT_OPTIONS``; these values override anything
            present in ``otter_config.json``
    """
    config_fp = os.path.join(autograder_dir, "source", "otter_config.json")
    if os.path.isfile(config_fp):
        with open(config_fp, encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    config["autograder_dir"] = autograder_dir

    runner = create_runner(config, **kwargs)

    if runner.get_option("logo"):
        # ASCII 8207 is an invisible non-whitespace character; this should prevent gradescope from
        # incorrectly left-stripping the whitespace at the beginning of the logo
        print(f"{chr(8207)}\n", LOGO_WITH_VERSION, "\n", sep="")

    abs_ag_path = os.path.abspath(runner.get_option("autograder_dir"))
    with chdir(abs_ag_path):        
        try:
            runner.prepare_files()
            scores = runner.run()
            with open("results/results.pkl", "wb+") as f:
                    pickle.dump(scores, f)

            output = scores.to_gradescope_dict(runner.get_options())

        except OtterRuntimeError as e:
            output = {
                "score": 0,
                "stdout_visibility": "hidden",
                "tests": [
                    {
                        "name": "Autograder Error",
                        "output": f"Otter encountered an error when grading this submission:\n\n{e}",
                    },
                ],
            }
            raise e

        finally:
            if "output" in vars():
                with open("./results/results.json", "w+") as f:
                    json.dump(output, f, indent=4)                

    print("\n\n", end="")

    df = pd.DataFrame(output["tests"])

    if runner.get_option("print_score"):
        total, possible = df["score"].sum(), df["max_score"].sum()
        if "score" in output:
            total, possible = output["score"], runner.get_option("points_possible") or possible
        perc = total / possible * 100
        print(f"Total Score: {total:.3f} / {possible:.3f} ({perc:.3f}%)\n")

    if runner.get_option("print_summary"):
        pd.set_option("display.max_rows", None)  # print all rows of the dataframe
        if "output" in df.columns:
            df.drop(columns=["output"], inplace=True)
        if "visibility" in df.columns:
            df.drop(columns=["visibility"], inplace=True)

        print(df)
