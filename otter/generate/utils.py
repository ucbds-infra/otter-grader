"""Utilities for Otter Generate"""

import os


def zip_folder(zf, path, prefix="", exclude=[]):
    """
    Recursively add the contents of a directory into a ``zipfile.ZipFile``.

    Args:
        zf (``zipfile.ZipFile``): the open zip file object to add to
        path (``str``): an absolute path to the directory to add to the zip file
        prefix (``str``, optional): a prefix to add to the basename of the path for the archive name
    """
    if not os.path.isabs(path):
        raise ValueError("'path' must be absolute path")

    parent_basename = os.path.basename(path)
    for file in os.listdir(path):
        if file in exclude:
            continue
        child_path = os.path.join(path, file)

        if os.path.isfile(child_path):
            arcname = os.path.join(prefix, parent_basename, file)
            zf.write(child_path, arcname=arcname)

        elif os.path.isdir(child_path):
            zip_folder(zf, child_path, prefix=os.path.join(prefix, parent_basename))
