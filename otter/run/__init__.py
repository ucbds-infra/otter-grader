"""
"""

import os
import json
import shutil
import pickle
import zipfile
import tempfile

from .run_autograder import main as run_autograder

def main(submission, autograder, output_dir, no_logo, debug, **kwargs):
    """
    """

    dp = tempfile.mkdtemp()

    try:
        ag_dir = os.path.join(dp, "autograder")

        for subdir in ["source", "submission", "results"]:
            path = os.path.join(ag_dir, subdir)
            os.makedirs(path, exist_ok=True)

        with open(os.path.join(ag_dir, "submission_metadata.json"), "w+") as f:
            json.dump({}, f)
        
        ag_zip = zipfile.ZipFile(autograder)
        ag_zip.extractall(os.path.join(ag_dir, "source"))
        ag_zip.close()

        shutil.copy(submission, os.path.join(ag_dir, "submission"))

        logo = not no_logo
        run_autograder(ag_dir, logo=logo, debug=debug)

        results_path = os.path.join(ag_dir, "results", "results.json")
        shutil.copy(results_path, output_dir)

        results_pkl_path = os.path.join(ag_dir, "results", "results.pkl")
        with open(results_pkl_path, "rb") as f:
            results = pickle.load(f)

    except:
        shutil.rmtree(dp)
        raise
    
    else:
        shutil.rmtree(dp)

    return results
