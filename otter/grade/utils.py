"""
Utilities for Otter Grade
"""

import tempfile
import tarfile
import os
import pandas as pd

from contextlib import contextmanager

@contextmanager
def simple_tar(path):
    f = tempfile.NamedTemporaryFile()
    t = tarfile.open(mode="w", fileobj=f)

    path = os.path.abspath(path)
    t.add(path, arcname=os.path.basename(path))

    t.close()
    f.seek(0)

    yield f

    f.close()

@contextmanager
def get_container_file(container, path):
    tarf = tempfile.NamedTemporaryFile()
    f = tempfile.NamedTemporaryFile()

    bits, _ = container.get_archive(path)
    for chunk in bits:
        tarf.write(chunk)

    tarf.seek(0)

    tar = tarfile.open(mode="r", fileobj=tarf)

    members = tar.getmembers()
    assert len(members) == 1, "Too many members to extract from container"
    file_contents = tar.extractfile(members[0])
    
    f.write(file_contents.read())
    tar.close()
    tarf.close()
    
    f.seek(0)

    yield f

    f.close()

def list_files(path):
    """Returns a list of all non-hidden files in a directory
    
    Args:
        path (``str``): path to a directory
    
    Returns:
        ``list`` of ``str``: list of filenames in the given directory

    """
    return [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)) and file[0] != "."]

def merge_csv(dataframes):
    """Merges dataframes along the vertical axis
    
    Args:
        dataframes (``list`` of ``pandas.core.frame.DataFrame``): list of dataframes with same columns
    
    Returns:
        ``pandas.core.frame.DataFrame``: A merged dataframe resulting from 'stacking' all input dataframes

    """
    final_dataframe = pd.concat(dataframes, axis=0, join='inner').sort_index()
    return final_dataframe
