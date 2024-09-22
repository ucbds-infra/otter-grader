"""Utilities for Otter Grade"""

import os
import pandas as pd
import re

from python_on_whales import docker

from ..test_files import GradingResults


OTTER_DOCKER_IMAGE_NAME = "otter-grade"

POINTS_POSSIBLE_LABEL = "points-per-question"

SCORES_DICT_FILE_KEY = "file"
SCORES_DICT_GRADING_STATUS_KEY = "grading_status"
SCORES_DICT_PERCENT_CORRECT_KEY = "percent_correct"
SCORES_DICT_TOTAL_POINTS_KEY = "total_points_earned"


class TimeoutException(Exception):
    """
    This Exception is thrown when grading a notebook exceeds the timeout value specified.
    """

    pass


def list_files(path: str) -> list[str]:
    """
    Returns a list of all non-hidden files in a directory

    Args:
        path (``str``): path to a directory

    Returns:
        ``list[str]``: list of filenames in the given directory

    """
    return [
        file
        for file in os.listdir(path)
        if os.path.isfile(os.path.join(path, file)) and file[0] != "."
    ]


def merge_csv(dataframes: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Merges dataframes along the vertical axis

    Args:
        dataframes (``list[pandas.core.frame.DataFrame]``): list of dataframes with same columns

    Returns:
        ``pandas.core.frame.DataFrame``: a merged dataframe resulting from 'stacking' all input
            dataframes

    """
    final_dataframe = pd.concat(dataframes, axis=0, join="inner")
    do_not_sort = final_dataframe[final_dataframe["file"] == POINTS_POSSIBLE_LABEL]
    sort_these = final_dataframe[final_dataframe["file"] != POINTS_POSSIBLE_LABEL]
    df_sorted = sort_these.sort_values(by="file")
    df_final = pd.concat([do_not_sort, df_sorted], ignore_index=True)
    return df_final


def prune_images(force: bool = False):
    """
    Prunes all Docker images named ``otter-grade``.
    """
    images = docker.images(OTTER_DOCKER_IMAGE_NAME)
    print("The following images will be deleted:")
    for image in images:
        print(f"    {image.repo_tags[0]}")

    if not force:
        sure = input(
            "Are you sure you want to delete these images? This action cannot be undone [y/N] "
        )
        sure = bool(re.match(r"ye?s?", sure, flags=re.IGNORECASE))

    else:
        sure = True

    if sure:
        for image in images:
            image.remove(force=True)

        print("Images deleted.")

    else:
        print("Prune cancelled.")


def get_points_possible_df(scores: list[GradingResults]) -> pd.DataFrame:
    """
    From the list of ``GradingResults`` objects try to find one that does not have a catastrophic
    failure and extract the points-per-question into its own DataFrame. This becomes the
    first row of final_grades.csv. If all the ``GradingResults`` objects  are catastrophic failures
    then returns an empty DataFrame

    Args:
        scores (``list[otter.test_files.GradingResults]``): the score objects to locate the points
            per question

    Returns:
        ``pd.DataFrame``: the points per question dataframe; if all failures empty dataframe
    """
    gr_completed = [s for s in scores if not s.has_catastrophic_failure()]
    pts_poss_df = pd.DataFrame()
    if gr_completed:
        pts_poss_dict = {t: [d["possible"]] for t, d in gr_completed[0].to_dict().items()}
        pts_poss_dict[SCORES_DICT_FILE_KEY] = [POINTS_POSSIBLE_LABEL]
        pts_poss_dict[SCORES_DICT_PERCENT_CORRECT_KEY] = [1]
        pts_poss_dict[SCORES_DICT_TOTAL_POINTS_KEY] = [gr_completed[0].possible]
        pts_poss_dict[SCORES_DICT_GRADING_STATUS_KEY] = ["--"]
        pts_poss_df = pd.DataFrame(pts_poss_dict)

    return pts_poss_df


def merge_scores_to_df(scores: list[GradingResults]) -> pd.DataFrame:
    """
    Convert a list of ``GradingResults`` objects to a scores dataframe, including a row
    with the total point values for each question.

    Args:
        scores (``list[otter.test_files.GradingResults]``): the score objects to merge

    Returns:
        ``pd.DataFrame``: the scores dataframe
    """
    dfs = []
    pts_poss_df = get_points_possible_df(scores)
    if not pts_poss_df.empty:
        dfs.append(pts_poss_df)

    for gr in scores:
        scores_dict = gr.to_dict()
        failed = gr.has_catastrophic_failure()
        if failed and not pts_poss_df.empty:
            scores_dict = {t: [0] for t in pts_poss_df.to_dict()}
        elif not failed:
            scores_dict = {t: [scores_dict[t]["score"]] for t in scores_dict}

        grading_status = "Completed" if not failed else str(gr.catastrophic_error)

        scores_dict[SCORES_DICT_TOTAL_POINTS_KEY] = gr.total
        scores_dict[SCORES_DICT_FILE_KEY] = gr.file
        scores_dict[SCORES_DICT_PERCENT_CORRECT_KEY] = gr.percent
        scores_dict[SCORES_DICT_GRADING_STATUS_KEY] = grading_status

        dfs.append(pd.DataFrame(scores_dict, index=[0]))

    output_df = merge_csv(dfs)
    cols = output_df.columns.tolist()
    question_cols = sorted(
        c
        for c in cols
        if c
        not in {
            SCORES_DICT_FILE_KEY,
            SCORES_DICT_TOTAL_POINTS_KEY,
            SCORES_DICT_PERCENT_CORRECT_KEY,
            SCORES_DICT_GRADING_STATUS_KEY,
        }
    )
    output_df = output_df[
        [
            SCORES_DICT_FILE_KEY,
            *question_cols,
            SCORES_DICT_TOTAL_POINTS_KEY,
            SCORES_DICT_PERCENT_CORRECT_KEY,
            SCORES_DICT_GRADING_STATUS_KEY,
        ]
    ]

    return output_df
