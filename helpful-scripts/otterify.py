##########################################
##### Otterifies Notebooks from OkPy #####
##########################################

# USAGE:
# Specify a path (either a .ipynb file or a directory) as the only argument to this script. If the path
# is a file, the file is converted from an OkPy-formatted notebook to an Otter-formatted notebook.
# If it is a directory, the directory and its children are recursively searched for IPYNB files which
# are all converted. THIS WILL OVERWRITE THE ORIGINAL FILES, so if you need to keep the originals, make
# sure to run this script on a COPY of the file, rather than the original!
# 
# To convert all IPYNBs in the current WD and its subdirectories:
#     python3 otterify.py .
# 
# To convert ./notebook.ipynb:
#     python3 otterify.py notebook.ipynb
# 
# To convert Gofer-formatted notebooks:
#     python3 otterify.py --from gofer .

import json
import sys
import re
import os
import argparse
import nbformat

REGEXES = {
    "ok": {
        "import": r"(# Initialize OK\n?)?from client\.api\.notebook import Notebook\nok = Notebook\([\"'].+\.ok[\"']\)",
        "check": r"ok\.grade\([\"'](.+)[\"']\);?",
        "auth": r"(_ = )?ok\.auth\((inline=True)?\);?",
        "submit": r"_ = ok\.submit\(\);?"
    },
    "gofer": {
        "import": r"from gofer\.ok import check",
        "check": r"check\([\"'](.+)\.py[\"']\)"
    }
}

def get_nb_paths(source):
    """Returns a list of paths to IPYNB files based on a directory SOURCE"""
    assert os.path.exists(source), f"Path {source} does not exist"
    if os.path.isfile(source):
        assert os.path.splitext(source)[1] == ".ipynb", "File specified is not IPYNB file"
        return source
    elif os.path.isdir(source):
        nb_paths = []
        for path in os.listdir(source):
            if os.path.isdir(os.path.join(source, path)):
                nb_paths.extend(get_nb_paths(os.path.join(source, path)))
            elif os.path.isfile(os.path.join(source, path)):
                if os.path.splitext(path)[1] == ".ipynb":
                    nb_paths.append(os.path.join(source, path))
        return nb_paths

if __name__ == "__main__":
    # parse args
    parser = argparse.ArgumentParser(description="Otterify notebookes from OkPy or Gofer format")
    parser.add_argument("--from", dest="from_format", type=str, default="ok", help="Original format of notebook; either 'ok' or 'gofer'")
    parser.add_argument("source", type=str, help="Path to IPYNB file or directory to recursively convert")
    args = parser.parse_args()

    # get regexes from REGEXES
    IMPORT_REGEX = REGEXES[args.from_format].get("import", None)
    CHECK_REGEX = REGEXES[args.from_format].get("check", None)
    AUTH_REGEX = REGEXES[args.from_format].get("auth", None)
    SUBMIT_REGEX = REGEXES[args.from_format].get("submit", None)

    for notebook in get_nb_paths(sys.argv[1]):
        print(f"Converting {notebook}")
        nb = nbformat.read(notebook, as_version=nbformat.NO_CONVERT)
        
        for cell in nb.cells:
            if cell.cell_type == 'code':
                # First, match on grader.check()
                if CHECK_REGEX is not None:
                    match = re.search(CHECK_REGEX, cell.source)
                    if match:
                        q_id = os.path.split(match[1])[1]
                        cell.source = re.sub(CHECK_REGEX, f"grader.check(\"{q_id}\")", cell.source)
                
                # Then, check the import
                if IMPORT_REGEX is not None:
                    match = re.search(IMPORT_REGEX, cell.source)
                    if match:
                        cell.source = re.sub(IMPORT_REGEX, "import otter\ngrader = otter.Notebook()", cell.source)
                
                # Then, check the auth
                if AUTH_REGEX is not None:
                    match = re.search(AUTH_REGEX, cell.source)
                    if match:
                        cell.source = re.sub(AUTH_REGEX, "", cell.source)
                
                # Finally, check the submit
                if SUBMIT_REGEX is not None:
                    match = re.search(SUBMIT_REGEX, cell.source)
                    if match:
                        cell.source = re.sub(SUBMIT_REGEX, "", cell.source)
        
        nbformat.write(nb, notebook, version=nbformat.NO_CONVERT)
