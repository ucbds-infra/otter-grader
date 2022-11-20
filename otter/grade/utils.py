"""Utilities for Otter Grade"""

from python_on_whales import docker
import os
import pandas as pd
import re

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

def prune_images(force=False):
    """
    Prunes all Docker images named ``otter-grade``
    """
    if not force:
        sure = input("Are you sure you want to prune Otter's grading images? This action cannot be undone [y/N] ")
        sure = bool(re.match(r"ye?s?", sure, flags=re.IGNORECASE))
    else:
        sure = True

    if sure:        
        images = docker.images()

        for img in images:
            if any([t.startswith(OTTER_DOCKER_IMAGE_TAG + ":") for t in img.repo_tags]):
                img.remove(force=True)

def generate_hash(path, extra_data):
    """
    Reads in a file and returns an MD5 hash of its contents.

    Args:
        path (``str``): path to the file that will be read in and hashed
        extra_data (``str``): extra data to add to the hash

    Returns:
        ``str``: the hash value of the file
    """
    m = md5()
    with open(path, "rb") as f:
        data = f.read()
        m.update(data)

    m.update(extra_data.encode("utf-8"))
    return m.hexdigest()
