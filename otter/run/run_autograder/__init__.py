"""Autograding process internals for Otter-Grader"""

import json
import os
import pandas as pd
import zipfile

from contextlib import nullcontext
from glob import glob
from typing import Any, Union

from .autograder_config import AutograderConfig
from .runners import create_runner
from .utils import capture_run_output, OtterRuntimeError, print_output
from ... import logging
from ...utils import chdir, OTTER_CONFIG_FILENAME
from ...version import LOGO_WITH_VERSION


__all__ = ["AutograderConfig", "capture_run_output", "main"]


LOGGER = logging.get_logger(__name__)


def main(autograder_dir: str, *, otter_run: bool = False, **kwargs: Any):
    """
    Run the autograding process.

    Args:
        autograder_dir (``str``): the absolute path of the directory in which autograding is occurring
            (e.g. on Gradescope, this is ``/autograder``)
        otter_run (``bool``): whether this function is being invoked by Otter Run (i.e. without
            containerization)
        **kwargs: keyword arguments for updating autograder configurations; these values override
            anything present in ``otter_config.json``
    """
    import dill

    config_fp = os.path.join(autograder_dir, "source", OTTER_CONFIG_FILENAME)
    if os.path.isfile(config_fp):
        with open(config_fp, encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    runner = create_runner(config, autograder_dir=autograder_dir, **kwargs)
    runner.ag_config.otter_run = otter_run

    ctx = nullcontext()
    if runner.ag_config.log_level is not None:
        ctx = logging.level_context(runner.ag_config.log_level)

    with ctx:
        LOGGER.debug(f"Detected containerized grading (T/F): {'F' if otter_run else 'T'}")
        LOGGER.debug(f"Config file path was resolved as: {config_fp}")
        LOGGER.debug(f"Autograder config was created: {runner.ag_config}")

        if runner.ag_config.logo:
            # U+8207 is an invisible non-whitespace character; this should prevent gradescope from
            # incorrectly left-stripping the whitespace at the beginning of the logo
            print_output(f"{chr(8207)}\n", LOGO_WITH_VERSION, "\n", sep="")

        abs_ag_path = os.path.abspath(runner.ag_config.autograder_dir)
        with chdir(abs_ag_path):
            try:
                if runner.ag_config.zips:
                    with chdir("./submission"):
                        zips = glob("*.zip")
                        if len(zips) > 1:
                            raise OtterRuntimeError(
                                "More than one zip file found in submission and 'zips' config is true"
                            )

                        with zipfile.ZipFile(zips[0]) as zf:
                            zf.extractall()

                runner.prepare_files()
                scores = runner.run()
                with open("results/results.pkl", "wb+") as f:
                    dill.dump(scores, f)

                output = scores.to_gradescope_dict(runner.ag_config)

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

        print_output("\n\n", end="")

        df = pd.DataFrame(output["tests"])

        if runner.ag_config.print_score and "score" in df.columns:
            total: Union[int, float]
            possible: Union[int, float]
            total, possible = df["score"].sum(), df["max_score"].sum()
            if "score" in output:
                total, possible = output["score"], runner.ag_config.points_possible or possible
            perc = total / possible * 100
            print_output(f"Total Score: {total:.3f} / {possible:.3f} ({perc:.3f}%)\n")

        if runner.ag_config.print_summary:
            pd.set_option("display.max_rows", None)  # print all rows of the dataframe
            if "output" in df.columns:
                df.drop(columns=["output"], inplace=True)
            if "visibility" in df.columns:
                df.drop(columns=["visibility"], inplace=True)
            if "status" in df.columns:
                df.drop(columns=["status"], inplace=True)

            print_output(df)
