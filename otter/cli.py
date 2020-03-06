###################################################
##### Command Line Interface for Otter-Grader #####
###################################################

import argparse
import pandas as pd
import os

from .metadata import *
from .containers import *
from .utils import *

def main():
	"""
	Main function for running otter from the command line.
	"""
	parser = argparse.ArgumentParser(description="""
	Local autograder for Jupyter Notebooks and Python scripts. Launches parallel Docker containers to grade notebooks/scripts and returns a CSV of grades.
	Requires a metadata file if not exported from Gradescope or Canvas. Add support files by putting them into the SUBMISSIONS-DIR folder or using the -f flag.
	Can optionally create PDFs of Jupyter Notebooks for manual grading.
	""")

	# necessary path arguments
	parser.add_argument("-p", "--path", dest="notebooks-path", type=str, default="./", help="Path to directory of submissions")
	parser.add_argument("-t", "--tests-path", dest="tests-path", type=str, default="./tests/", help="Path to directory of tests")
	parser.add_argument("-o", "--output-path", dest="output-path", type=str, default="./", help="Path to which to write output")
	
	# metadata parser arguments
	parser.add_argument("-g", "--gradescope", action="store_true", default=False, help="Flag for Gradescope export")
	parser.add_argument("-c", "--canvas", action="store_true", default=False, help="Flag for Canvas export")
	parser.add_argument("-j", "--json", default=False, help="Flag for path to JSON metadata")
	parser.add_argument("-y", "--yaml", default=False, help="Flag for path to YAML metadata")
	
	# script grading argument
	parser.add_argument("-s", "--scripts", action="store_true", default=False, help="Flag to incidicate grading Python scripts")

	# PDF export options
	parser.add_argument("--pdf", action="store_true", default=False, help="Create unfiltered PDFs for manual grading")
	parser.add_argument("--tag-filter", dest="tag-filter", action="store_true", default=False, help="Create a tag-filtered PDF for manual grading")
	parser.add_argument("--html-filter", dest="html-filter", action="store_true", default=False, help="Create an HTML comment-filtered PDF for manual grading")

	# other settings and optional arguments
	parser.add_argument("-f", "--files", nargs="+", help="Specify support files needed to execute code (e.g. utils, data files)")
	parser.add_argument("-v", "--verbose", action="store_true", help="Flag for verbose output")
	parser.add_argument("-r", "--requirements", default="requirements.txt", type=str, help="Flag for Python requirements file path; ./requirements.txt automatically checked")
	parser.add_argument("--containers", dest="num-containers", type=int, help="Specify number of containers to run in parallel")
	parser.add_argument("--image", default="ucbdsinfra/otter-grader", help="Custom docker image to run on")
	parser.add_argument("--no-kill", dest="no-kill", action="store_true", default=False, help="Do not kill containers after grading")
	
	# parse args
	params = vars(parser.parse_args())

	# Asserts that exactly one metadata flag is provided
	assert sum([meta != False for meta in [params["gradescope"], 
		params["canvas"], 
		params["json"], 
		params["yaml"]]]) == 1, "You must supply exactly one metadata flag (-g, -j, -y, -c)"

	# Asserts that either --pdf, --tag-filter, or --html-filter but not both provided
	assert sum([params["pdf"], params["tag-filter"], params["html-filter"]]) <= 1, "Cannot provide more than 1 PDF flag"

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
		meta_parser = JSONParser(os.path.join(params["json"]))
		if verbose:
			print("Found JSON metadata...")
	else:
		meta_parser = YAMLParser(os.path.join(params["yaml"]))
		if verbose:
			print("Found YAML metadata...")

	# check that reqs file is valid
	if not (os.path.exists(params["requirements"]) and os.path.isfile(params["requirements"])):
		
		# if user-specified requirements not found, fail with AssertionError
		if params["requirements"] != "requirements.txt":
			assert False, "requirements file {} does not exist".format(params["requirements"])

		# else just set to None and reqs are ignored
		params["requirements"] = None

	if verbose:
		print("Launching docker containers...")

	# Docker
	grades_dfs = launch_parallel_containers(params["tests-path"], 
		params["notebooks-path"], 
		verbose=verbose, 
		unfiltered_pdfs=params["pdf"], 
		tag_filter=params["tag-filter"],
		html_filter=params["html-filter"],
		reqs=params["requirements"],
		num_containers=params["num-containers"],
		image=params["image"],
		scripts=params["scripts"],
		no_kill=params["no-kill"]
	)

	if verbose:
		print("Combining grades and saving...")

	# Merge Dataframes
	output_df = merge_csv(grades_dfs)

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

if __name__ == "__main__":
	main()
