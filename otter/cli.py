#!/usr/bin/env python

import argparse
import pandas as pd
import os

from .metadata import *
from .docker import *
from .parallel import *

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-g", "--gradescope", action="store_true", default=False, help="Flag for Gradescope export")
	parser.add_argument("-c", "--canvas", action="store_true", default=False, help="flag for Canvas export")
	parser.add_argument("-j", "--json", default=False, help="Flag for path to JSON metadata")
	parser.add_argument("-y", "--yaml", default=False, help="Flag for path to YAML metadata")
	parser.add_argument("-n", "--notebooks-path", dest="notebooks-path", type=str, default="./", help="Path to directory of notebooks")
	parser.add_argument("-t", "--tests-path", dest="tests-path", type=str, default="./tests/", help="Path to directory of tests")
	parser.add_argument("-o", "--output-path", dest="output-path", type=str, default="./", help="Path to which to write output")
	parser.add_argument("-v", "--verbose", action="store_true", help="Flag for verbose output")
	parser.add_argument("-r", "--requirements", type=str, help="Flag for Python requirements file path")
	parser.add_argument("--containers", dest="num-containers", type=int, help="Specify number of containers to run in parallel")
	parser.add_argument("--pdf", action="store_true", default=False, help="Create PDFs as manual-graded submissions")
	params = vars(parser.parse_args())

	# Asserts that exactly one metadata flag is provided
	assert sum([meta != False for meta in [params["gradescope"], 
		params["canvas"], 
		params["json"], 
		params["yaml"]]]) == 1, "You must supply exactly one metadata flag (-g, -j, -y, -c)"

	# verbose flag
	verbose = params["verbose"]

	# Hand off metadata to parser
	if params["gradescope"]:
		meta_parser = GradescopeParser(params["notebooks-path"])
		if verbose:
			print("Found Gradescope metadata...")
	elif params["canvas"]:
		meta_parser = CanvasParser(params["notebooks-path"])
		if verbose:
			print("Found Canvas metadata...")
	elif params["json"]:
		meta_parser = JSONParser(os.path.join(params["notebooks-path"], params["json"]))
		if verbose:
			print("Found JSON metadata...")
	else:
		meta_parser = YAMLParser(os.path.join(params["notebooks-path"], params["yaml"]))
		if verbose:
			print("Found YAML metadata...")

	# check that reqs file is valid
	if params["requirements"]:
		assert os.path.exists(params["requirements"]) and \
			os.path.isfile(params["requirements"]), "Requirements file '{}' does not exist.".format(params["requirements"])

	if verbose:
		print("Launching docker containers...")

	# Docker
	grades_dfs = launch_parallel_containers(params["tests-path"], 
		params["notebooks-path"], 
		verbose=verbose, 
		pdfs=params["pdf"], 
		reqs=params["requirements"],
		num_containers=params["num-containers"]
	)

	if verbose:
		print("Combining grades and saving...")

	# Merge Dataframes
	output_df = merge_csv(grades_dfs, params["output-path"])

	def map_files_to_ids(row):
		"""Returns the identifier for the filename in the specified row"""
		return meta_parser.file_to_id(row["file"])

	# add in identifier column
	output_df["identifier"] = output_df.apply(map_files_to_ids, axis=1)

	# reorder cols in output_df
	cols = output_df.columns.tolist()
	output_df = output_df[cols[-1:] + cols[:-1]]

	# write to CSV file
	output_df.to_csv(os.path.join(params["output-path"], "final_grades.csv"), index=False)


# Exports a list of dataframes as a single, merged csv file
def merge_csv(dataframes, output_path):
	"""Merges dataframes returned by Docker containers"""
	final_dataframe = pd.concat(dataframes, axis=0, join='inner').sort_index()
	return final_dataframe
