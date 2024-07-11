"""Utilities for Otter Grade"""

import os
import pandas as pd
import re

from typing import List
from python_on_whales import docker

from ..test_files import GradingResults

OTTER_DOCKER_IMAGE_NAME = "otter-grade"

POINTS_POSSIBLE_LABEL = "points-per-question"

SCORES_DICT_FILE_KEY = "file"

SCORES_DICT_TOTAL_POINTS_KEY = "total_points_earned"

SCORES_DICT_PERCENT_CORRECT_KEY = "percent_correct"


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


def merge_scores_to_df(scores: List[GradingResults]) -> pd.DataFrame:  
    """  
    Convert a list of ``GradingResults`` objects to a scores dataframe, including a row  
    with the total point values for each question.  

    Args:  
        scores (``list[otter.test_files.GradingResults]``): the score objects to merge  

    Returns:  
        ``pd.DataFrame``: the scores dataframe  
    """
    full_df = []
    pts_poss_dict = {t: [scores[0].to_dict()[t]["possible"]] for t in scores[0].to_dict()}
    pts_poss_dict[SCORES_DICT_FILE_KEY] = POINTS_POSSIBLE_LABEL
    pts_poss_dict[SCORES_DICT_PERCENT_CORRECT_KEY] = "NA"
    pts_poss_dict[SCORES_DICT_TOTAL_POINTS_KEY] = scores[0].possible
    pts_poss_df = pd.DataFrame(pts_poss_dict)
    full_df.append(pts_poss_df)
    for grading_result in scores:
        scores_dict = grading_result.to_dict()
        scores_dict = {t: [scores_dict[t]["score"]] for t in scores_dict}
        scores_dict[SCORES_DICT_PERCENT_CORRECT_KEY] = round(grading_result.total / grading_result.possible, 4)
        scores_dict[SCORES_DICT_TOTAL_POINTS_KEY] = grading_result.total
        scores_dict[SCORES_DICT_FILE_KEY] = grading_result.file
        df_scores = pd.DataFrame(scores_dict)
        full_df.append(df_scores)
    return full_df
