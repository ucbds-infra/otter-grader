import os
import shutil
import argparse
from glob import glob

RUN_AUTOGRADER = """#!/usr/bin/env python3

from otter.grade import grade_notebook
from glob import glob
import json
import os
import shutil

if __name__ == "__main__":
	# put files into submission directory
	if os.path.exists("/autograder/source/files"):
		for filename in glob("/autograder/source/files/*.*"):
			shutil.copy(filename, "/autograder/submission")

	os.chdir("/autograder/submission")
	nb_path = glob("*.ipynb")[0]
	scores = grade_notebook(nb_path, "/autograder/source/tests/*.py")

	output = {{}}
	output["score"] = scores["total"]
	output["visibility"] = "hidden"

	with open("/autograder/results/results.json", "w+") as f:
		json.dump(output, f)
"""

REQUIREMENTS = """datascience
jupyter_client
ipykernel
matplotlib
pandas
ipywidgets
scipy
gofer-grader==1.0.3
nb2pdf==0.0.2
otter-grader==0.0.11
"""

SETUP_SH = """#!/usr/bin/env bash

apt-get install -y python3 python3-pip

pip3 install -r /autograder/source/requirements.txt
"""

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--tests-path", dest="tests-path", type=str, default="./tests/")
	parser.add_argument("-o", "--output-path", dest="output-path", type=str, default="./")
	# parser.add_argument("-v", "--verbose", action="store_true")
	parser.add_argument("-r", "--requirements", type=str)
	parser.add_argument(dest="files", nargs=argparse.REMAINDER)
	params = vars(parser.parse_args())

	# create tmp directory to zip inside
	os.mkdir("./tmp")

	# copy tests into tmp
	os.mkdir(os.path.join("tmp", "tests"))
	for file in glob(os.path.join(params["tests-path"], "*.py")):
		shutil.copy(file, os.path.join(os.getcwd(), "tmp", "tests"))

	reqs = REQUIREMENTS

	if params["requirements"]:
		with open(params["requirements"]) as f:
			reqs += f.read()

	# copy requirements into tmp
	with open(os.path.join(os.getcwd(), "tmp", "requirements.txt"), "w+") as f:
		f.write(reqs)

	# write setup.sh and run_autograder to tmp
	with open(os.path.join(os.getcwd(), "tmp", "setup.sh"), "w+") as f:
		f.write(SETUP_SH)

	with open(os.path.join(os.getcwd(), "tmp", "run_autograder"), "w+") as f:
		f.write(RUN_AUTOGRADER)

	# copy files into tmp
	if params["files"]:
		os.mkdir(os.path.join("tmp", "files"))

		for file in files:
			shutil.copy(file, os.path.join(os.getcwd(), "tmp", "files", os.path.split(file)[1]))

	os.chdir("./tmp")

	zip_cmd = ["zip", os.path.join("..", params["output-path"], "autograder.zip"), "run_autograder",
			   "setup.sh", "requirements.txt", "tests"]

	if params["files"]:
		zip_cmd += ["files"]

	zipped = subprocess.run(zip_cmd, stdout=PIPE, stderr=PIPE)

	if zipped.stderr.decode("utf-8"):
		raise Exception(zipped.stderr.decode("utf-8"))