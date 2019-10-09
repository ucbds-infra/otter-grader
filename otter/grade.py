#!/usr/bin/env python

import argparse
import os
from os.path import isfile, join
from glob import glob
from gofer.ok import grade_notebook
import pandas as pd
import nb2pdf
import re

def grade(ipynb_path, pdf):
	base_path = os.path.dirname(ipynb_path)
	test_files = glob('/home/tests/*.py')
	result = grade_notebook(ipynb_path, test_files)
	if pdf:
		nb2pdf.convert(ipynb_path)
	return result

def main():
	argparser = argparse.ArgumentParser()
	argparser.add_argument('notebook_directory', help='Path to directory with ipynb\'s to grade')
	argparser.add_argument("--pdf", action="store_true", default=False)
	args = argparser.parse_args()
	dir_path = os.path.abspath(args.notebook_directory)
	os.chdir(os.path.dirname(dir_path))
	all_ipynb = [(f, join(dir_path, f)) for f in os.listdir(dir_path) if isfile(join(dir_path, f)) and f[-6:] == ".ipynb"]

	all_results = {"file": [], "score": [], "manual": []}
	
	if not args.pdf:
		del all_results["manual"]
	
	for ipynb_name, ipynb_path in all_ipynb:
		all_results["file"].append(ipynb_name)
		score = grade(ipynb_path, args.pdf)
		all_results["score"].append(score)
		if args.pdf:
			pdf_path = re.sub(r"\.ipynb$", ".pdf", ipynb_path)
			all_results["manual"].append(pdf_path)

	final_results = pd.DataFrame(all_results)
	final_results.to_csv("grades.csv", index=False)

if __name__ == "__main__":
	main()