from .docker import grade_assignments
from concurrent.futures import ThreadPoolExecutor, wait
import os
import shutil
from subprocess import PIPE
import subprocess
import time

def launch_parallel_containers(tests_dir, notebooks_dir, verbose=False, pdfs=False, reqs=None, num_containers=None, image="ucbdsinfra/otter-grader", scripts=False):
	"""Grades notebooks in parallel docker containers"""
	if not num_containers:
		num_containers = 4

	# list all notebooks in the dir
	dir_path = os.path.abspath(notebooks_dir)
	file_extension = (".py", ".ipynb")[not scripts]
	notebooks = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)) and f.endswith(file_extension)]

	# set indices of notebooks
	num_per_group = int(len(notebooks) / num_containers)

	for i in range(num_containers):
		os.mkdir(os.path.join(dir_path, "tmp{}".format(i)))

		# copy all non-notebook files into each tmp directory
		for file in os.listdir(dir_path):
			if os.path.isfile(os.path.join(dir_path, file)) and not file.endswith(file_extension):
				shutil.copy(os.path.join(dir_path, file), os.path.join(dir_path, "tmp{}".format(i)))

	for k, v in enumerate(notebooks):
		shutil.copy(v, os.path.join(dir_path, "tmp{}".format(k % num_containers)))

	# execute containers in parallel
	pool = ThreadPoolExecutor(num_containers)
	futures = []
	for i in range(num_containers):
		futures += [pool.submit(grade_assignments, 
			tests_dir, 
			os.path.join(dir_path, "tmp{}".format(i)), 
			str(i), 
			verbose=verbose, 
			pdfs=pdfs, 
			reqs=reqs,
			image=image,
			scripts=scripts)]

	# stop execution while containers are running
	finished_futures = wait(futures)

	# clean up tmp directories
	for i in range(num_containers):
		shutil.rmtree(os.path.join(dir_path, "tmp{}".format(i)))

	# return list of dataframes
	return [df.result() for df in finished_futures[0]]
