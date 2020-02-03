######################################
##### Utilities for Otter-Grader #####
######################################

import os
import pandas as pd
import re

SUB_BEFORE_ASTERISK = r"(.*\n)*^\s*\*"
HTML_TAG_REGEX = r"</?[\w\" \d=:#%;'&-]*>"

def list_files(path):
	"""Returns a list of all non-hidden files in a directory"""
	return [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)) and file[0] != "."]

def merge_csv(dataframes, output_path):
	"""Merges dataframes returned by Docker containers"""
	final_dataframe = pd.concat(dataframes, axis=0, join='inner').sort_index()
	return final_dataframe

# def remove_html_in_hint(hint):
# 	hint = re.sub(
# 		SUB_BEFORE_ASTERISK,
# 		"",
# 		hint,
# 		flags=re.MULTILINE
# 	)
# 	hint = re.sub(
# 		HTML_TAG_REGEX,
# 		"",
# 		hint,
# 		flags=re.MULTILINE
# 	)
# 	hint = hint.strip() + "\n\n"
# 	return hint
