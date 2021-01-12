"""
Gradescope autograding internals for R
"""

import os
import json
import shutil
import nbformat
import jupytext

from glob import glob
from rpy2.robjects import r

from ..constants import DEFAULT_OPTIONS
from ..utils import get_source

NBFORMAT_VERSION = 4

def insert_seeds(nb_path, seed):
    """
    Adds calls to ``set.seed`` in a Jupyter notebook

    Args:
        nb_path (``str``): path to notebook to seed
        seed (``int``): the seed to set
    """
    nb = nbformat.read(nb_path, as_version=NBFORMAT_VERSION)
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = get_source(cell)
            source = [f"set.seed({seed})"] + source
            cell['source'] = "\n".join(source)
    nbformat.write(nb, nb_path)

def run_autograder(options):
    """
    Runs autograder for R assignments based on predefined configurations

    Args:
        options (``dict``): configurations for autograder; should contain all keys present in
            ``otter.run.run_adapter.constants.DEFAULT_OPTIONS``
        
    Returns:
        ``dict``: the results of grading as a JSON object
    """
    # options = DEFAULT_OPTIONS.copy()
    # options.update(config)

    abs_ag_path = os.path.abspath(options["autograder_dir"])
    os.chdir(abs_ag_path)

    # put files into submission directory
    if os.path.exists("./source/files"):
        for file in os.listdir("./source/files"):
            fp = os.path.join("./source/files", file)
            if os.path.isdir(fp):
                shutil.copytree(fp, os.path.join("./submission", os.path.basename(fp)))
            else:
                shutil.copy(fp, "./submission")

    os.chdir("./submission")

    # convert ipynb files to Rmd files
    if glob("*.ipynb"):
        fp = glob("*.ipynb")[0]
        if options["seed"] is not None:
            assert isinstance(options["seed"], int), f"{options['seed']} is an invalid seed"
            insert_seeds(fp, options["seed"])
        nb = jupytext.read(fp)
        jupytext.write(nb, os.path.splitext(fp)[0] + ".Rmd")
    
    # convert Rmd files to R files
    if glob("*.Rmd"):
        fp = glob("*.Rmd")[0]
        fp, wp = os.path.abspath(fp), os.path.abspath(os.path.splitext(fp)[0] + ".r")
        r(f"knitr::purl('{fp}', '{wp}')")

    # get the R script
    fp = glob("*.[Rr]")[0]

    os.makedirs("./tests", exist_ok=True)
    tests_glob = glob("../source/tests/*.[Rr]")
    for file in tests_glob:
        shutil.copy(file, "./tests")

    output = r(f"""ottr::run_gradescope("{fp}")""")[0]
    output = json.loads(output)
    
    if options["show_stdout"]:
        output["stdout_visibility"] = "after_published"

    os.chdir(abs_ag_path)

    return output
