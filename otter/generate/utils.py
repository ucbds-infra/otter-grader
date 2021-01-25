"""
"""

import os

def zip_folder(zf, path, prefix=""):
    """
    """
    if not os.path.isabs(path):
        raise ValueError("'path' must be absolute path")
    parent_basename = os.path.basename(path)
    for file in os.listdir(path):
        child_path = os.path.join(path, file)
        if os.path.isfile(child_path):
            arcname = os.path.join(prefix, parent_basename, file)
            zf.write(child_path, arcname=arcname)
        elif os.path.isdir(child_path):
            zip_folder(zf, child_path, prefix=os.path.join(prefix, parent_basename))
