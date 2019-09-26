#!/usr/bin/env python

import argparse
import pandas as pd
import os

from metadata import *
from docker import *

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
	params = vars(parser.parse_args())

	# Asserts that exactly one metadata flag is provided
	assert sum([meta != False for meta in [params["gradescope"], 
		params["canvas"], 
		params["json"], 
		params["yaml"]]]) == 1, "You must supply exactly one metadata flag (-g, -j, -y, -c)"

	# Hand off metadata to parser
	if params["gradescope"]:
		meta_parser = GradescopeParser(params["notebooks-path"])
	elif params["canvas"]:
		meta_parser = CanvasParser(params["notebooks-path"])
	elif params["json"]:
		meta_parser = JSONParser(os.path.join(params["notebooks-path"], params["json"]))
	else:
		meta_parser = YAMLParser(os.path.join(params["notebooks-path"], params["yaml"]))

	# Docker
	grades_df = grade_assignments(params["tests-path"], params["notebooks-path"], "42")

	# Merge Dataframes
	merge_export_csv([grades_df], params["output-path"])


# Exports a list of dataframes as a single, merged csv file
def merge_export_csv(dataframes, output_path):
	original_directory = os.getcwd()
	os.chdir(output_path)
	final_dataframe = pd.concat(dataframes, axis=1, join='inner').sort_index()
	final_dataframe.to_csv("final_grades.csv", index=False)
	os.chdir(original_directory)

if __name__ == "__main__":
	main()
