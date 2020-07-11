import re
import nbformat

from ..assign.utils import get_source

def replace_notebook_instances(nb_path):
    nb = nbformat.read(nb_path, as_version=nbformat.NO_CONVERT)

    instance_regex = r"otter.Notebook\([\"'].+[\"']\)"
    for cell in nb['cells']:
        source = get_source(cell)
        for i, line in enumerate(source):
            line = re.sub(instance_regex, line)
            source[i] = line
        cell['source'] = "\n".join(source)

    nbformat.write(nb, nb_path)
