"""Utilities for Otter Grade"""

import docker
import os
import pandas as pd

from hashlib import md5


OTTER_DOCKER_IMAGE_TAG = "otter-grade"


def list_files(path):
    """
    Returns a list of all non-hidden files in a directory
    
    Args:
        path (``str``): path to a directory
    
    Returns:
        ``list`` of ``str``: list of filenames in the given directory

    """
    return [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)) and file[0] != "."]

def merge_csv(dataframes):
    """
    Merges dataframes along the vertical axis
    
    Args:
        dataframes (``list`` of ``pandas.core.frame.DataFrame``): list of dataframes with same columns
    
    Returns:
        ``pandas.core.frame.DataFrame``: A merged dataframe resulting from 'stacking' all input dataframes

    """
    final_dataframe = pd.concat(dataframes, axis=0, join='inner').sort_index()
    return final_dataframe

def prune_images():
    """
    Prunes all Docker images named ``otter-grade``
    """
    # this is a fix for travis -- allows overriding docker client version
    if os.environ.get("OTTER_DOCKER_CLIENT_VERSION") is not None:
        client = docker.from_env(version=os.environ.get("OTTER_DOCKER_CLIENT_VERSION"))
    else:
        client = docker.from_env()
    
    images = client.images.list()

    for img in images:
        if any([OTTER_DOCKER_IMAGE_TAG in t for t in img.tags]):
            client.images.remove(img.tags[0], force=True)

def generate_hash(path):
    """
    Reads in a file and returns an MD5 hash of its contents.

    Args:
        path (``str``): path to the file that will be read in and hashed

    Returns:
        ``str``: the hash value of the file
    """
    zip_hash = ""
    m = md5()
    with open(path, "rb") as f:
        data = f.read() # read file in chunk and call update on each chunk if file is large.
        m.update(data)
        zip_hash = m.hexdigest()
    return zip_hash
