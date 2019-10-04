#!/usr/bin/env python

import argparse
import os
from os.path import isfile, join
from glob import glob
from gofer.ok import grade_notebook
import pandas as pd

def grade(ipynb_path):
    base_path = os.path.dirname(ipynb_path)
    test_files = glob(os.path.join(base_path, 'tests/*.py'))
    result = grade_notebook(ipynb_path, test_files)
    return result

def main():
	argparser = argparse.ArgumentParser()
	argparser.add_argument('notebook_directory', help='Path to directory with ipynb\'s to grade')
	args = argparser.parse_args()
	dir_path = os.path.abspath(args.notebook_directory)
	os.chdir(os.path.dirname(dir_path))
	all_ipynb = [(f, join(mypath, f)) for f in os.listdir(dir_path) if isfile(join(mypath, f))]

	all_results = {"file": [], "score": []}
	for ipynb_name, ipynb_path in all_ipynb:
	    all_results["file"].append(ipynb_name)
	    all_results["score"].append(grade(ipynb_path))

	final_results = pd.DataFrame(all_results)
	final_results.to_csv("grades.csv")

if __name__ == "__main__":
	main()