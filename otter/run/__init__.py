"""
"""

import os
import zipfile
import tempfile

def main(args):
    """
    """

    dp = tempfile.mkdtemp()
    ag_dir = os.path.join(dp, "autograder")

    for subdir in ["source", "submission"]:
        path = os.path.join(ag_dir, subdir)
        os.makedirs(path, exist_ok=True)
    

