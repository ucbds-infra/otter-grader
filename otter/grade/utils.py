"""Utilities for Otter Grade"""

import os
import pandas as pd
import re

from python_on_whales import docker


OTTER_DOCKER_IMAGE_NAME = "otter-grade"

POINTS_POSSIBLE_LABEL = "points-per-question"

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
    final_dataframe = pd.concat(dataframes, axis=0, join='inner')
    do_not_sort = final_dataframe[final_dataframe['file'] == POINTS_POSSIBLE_LABEL]
    sort_these = final_dataframe[final_dataframe['file'] != POINTS_POSSIBLE_LABEL]
    df_sorted = sort_these.sort_values(by="file")
    df_final = pd.concat([do_not_sort, df_sorted], ignore_index=True)
    return df_final


def prune_images(force=False):
    """
    Prunes all Docker images named ``otter-grade``.
    """
    images = docker.images(OTTER_DOCKER_IMAGE_NAME)
    print("The following images will be deleted:")
    for image in images:
        print(f"    {image.repo_tags[0]}")

    if not force:
        sure = input("Are you sure you want to delete these images? This action cannot be undone [y/N] ")
        sure = bool(re.match(r"ye?s?", sure, flags=re.IGNORECASE))

    else:
        sure = True

    if sure:        
        for image in images:
            image.remove(force=True)

        print("Images deleted.")

    else:
        print("Prune cancelled.")
