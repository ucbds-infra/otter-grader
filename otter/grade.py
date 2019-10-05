#!/usr/bin/env python

import argparse
import os
from os.path import isfile, join
from glob import glob
from gofer.ok import grade_notebook
import pandas as pd
import nb2pdf
import re

def grade(ipynb_path):
	base_path = os.path.dirname(ipynb_path)
	# assert False, ipynb_path
	test_files = glob('/home/tests/*.py')
	# with open(ipynb_path) as f:
	# 	os.listdir(base_path)
	# 	print(ipynb_path)
	# 	print(f.read())
	result = grade_notebook(ipynb_path, test_files)
	nb2pdf.convert(ipynb_path)
	return result

def main():
	argparser = argparse.ArgumentParser()
	argparser.add_argument('notebook_directory', help='Path to directory with ipynb\'s to grade')
	args = argparser.parse_args()
	dir_path = os.path.abspath(args.notebook_directory)
	os.chdir(os.path.dirname(dir_path))
	all_ipynb = [(f, join(dir_path, f)) for f in os.listdir(dir_path) if isfile(join(dir_path, f)) and f[-6:] == ".ipynb"]

	all_results = {"file": [], "score": [], "manual": []}
	for ipynb_name, ipynb_path in all_ipynb:
	    all_results["file"].append(ipynb_name)
	    score = grade(ipynb_path)
	    pdf_path = re.sub(r"\.ipynb$", ".pdf", ipynb_path)
	    all_results["score"].append(score)
	    all_results["manual"].append(pdf_path)

	final_results = pd.DataFrame(all_results)
	final_results.to_csv("grades.csv", index=False)

if __name__ == "__main__":
	main()