from .docker import grade_assignments
from concurrent.futures import ThreadPoolExecutor, wait
import os
import shutil
from subprocess import PIPE
import subprocess
import time

def launch_parallel_containers(tests_dir, notebooks_dir, verbose=False, pdfs=False, reqs=None, num_containers=None):
	"""Grades notebooks in parallel docker containers"""
	if not num_containers:
		num_containers = 4

	# list all notebooks in the dir
	dir_path = os.path.abspath(notebooks_dir)
	# os.chdir(os.path.dirname(dir_path))
	notebooks = [(f, os.path.join(dir_path, f)) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)) and f[-6:] == ".ipynb"]

	# set indices of notebooks
	num_per_group = int(len(notebooks) / num_containers)

	# copy notebooks into tmp directories
	for i in range(num_containers + 1):
		os.mkdir(os.path.join(dir_path, "tmp{}".format(i)))
		for j in range(i * num_per_group, (i+1) * num_per_group):
			try:
				cp_cmd = ["cp", notebooks[j][1], os.path.join(dir_path, "tmp{}".format(i))]
			except IndexError:
				break
			cp = subprocess.run(cp_cmd, stdout=PIPE, stderr=PIPE)
			if cp.stderr.decode("utf-8"):
				raise Exception(f"Error copying {notebooks[j]} into the tmp{j} directory.")

		# copy all non-notebook files into each tmp directory
		for file in os.listdir(dir_path):
			if os.path.isfile(os.path.join(dir_path, file)) and file[:-6] != ".ipynb":
				shutil.copy(os.path.join(dir_path, file), os.path.join(dir_path, "tmp{}".format(i)))

	# execute containers in parallel
	pool = ThreadPoolExecutor(num_containers + 1)
	futures = []
	for i in range(num_containers + 1):
		futures += [pool.submit(grade_assignments, 
			tests_dir, 
			os.path.join(dir_path, "tmp{}".format(i)), 
			str(i), 
			verbose=verbose, 
			pdfs=pdfs, 
			reqs=reqs)]

	# stop execution while containers are running
	finished_futures = wait(futures)

	# clean up tmp directories
	for i in range(num_containers + 1):
		shutil.rmtree(os.path.join(dir_path, "tmp{}".format(i)))

	# return list of dataframes
	return [df.result() for df in finished_futures[0]]
