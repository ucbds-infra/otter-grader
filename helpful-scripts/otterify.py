###########################################
##### Otterifies Notebooks from Gofer #####
###########################################

import json
import sys
import nbformat
import re
import os

GOFER_IMPORT_REGEX = r"from gofer\.ok import check"
GOFER_REGEX = r"check\([\"'](.+)\.py[\"']\)"

for notebook in sys.argv[1:]:
    print(f"Converting {notebook}")
    nb = nbformat.read(notebook, as_version=nbformat.NO_CONVERT)
    
    for cell in nb.cells:
        if cell.cell_type == 'code':
            match = re.search(GOFER_REGEX, cell.source)
            if match:
                q_id = os.path.split(match[1])[1]
                cell.source = re.sub(GOFER_REGEX, f"grader.check(\"{q_id}\")", cell.source)
            match = re.search(GOFER_IMPORT_REGEX, cell.source)
            if match:
                cell.source = re.sub(GOFER_IMPORT_REGEX, "import otter\ngrader = otter.Notebook()", cell.source)

    nbformat.write(nb, notebook)
