#!/usr/bin/env python

import argparse
import pandas as pd
import os

from .metadata import *
from .docker import *

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-g", "--gradescope", action="store_true", default=False,)
	parser.add_argument("-c", "--canvas", action="store_true", default=False)
	parser.add_argument("-j", "--json", default=False)
	parser.add_argument("-y", "--yaml", default=False)
	parser.add_argument("-n", "--notebooks-path", dest="notebooks-path", type=str, default="./")
	parser.add_argument("-t", "--tests-path", dest="tests-path", type=str, default="./tests/")
	parser.add_argument("-o", "--output-path", dest="output-path", type=str, default="./")
	parser.add_argument("-v", "--verbose", action="store_true")
	parser.add_argument("-r", "--requirements", type=str)
	parser.add_argument("--pdf", action="store_true", default=False)
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
	grades_df = grade_assignments(params["tests-path"], 
		params["notebooks-path"], 
		"42", 
		verbose=verbose, 
		pdfs=params["pdf"], 
		reqs=params["requirements"]
	)

	if verbose:
		print("Combining grades and saving...")

	# Merge Dataframes
	output_df = merge_export_csv([grades_df], params["output-path"])

	def map_files_to_ids(row):
		"""Returns the identifier for the filename in the specified row"""
		return meta_parser.file_to_id(row["file"])

	# add in identifier column
	output_df["identifier"] = output_df.apply(map_files_to_ids, axis=1)

	# write to CSV file
	output_df.to_csv(os.path.join(params["output-path"], "final_grades.csv"), index=False)


# Exports a list of dataframes as a single, merged csv file
def merge_export_csv(dataframes, output_path):
	original_directory = os.getcwd()
	os.chdir(output_path)
	final_dataframe = pd.concat(dataframes, axis=1, join='inner').sort_index()
	os.chdir(original_directory)
	return final_dataframe
