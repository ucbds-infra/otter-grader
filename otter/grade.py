###################################################
##### Command Line Interface for Otter-Grader #####
###################################################

import os
import pandas as pd
import re
import subprocess
from subprocess import PIPE

from .metadata import GradescopeParser, CanvasParser, JSONParser, YAMLParser
from .containers import launch_parallel_containers
from .utils import merge_csv

def grade_assignment(tests_dir, notebook_path, id, verbose=False, 
unfiltered_pdfs=False, tag_filter=False, html_filter=False, reqs=None, scripts=False, no_kill=False):
	"""
	Taken from https://github.com/ucbds-infra/otter-grader/blob/master/otter

	id should correspond to the tag generated in the instructor setup script
	"""

	# Get image id from tag
	docker_ls_command = ["docker", "image", "ls"]
	grep_command = ["grep", id]
	docker_ls = subprocess.Popen(docker_ls_command, stdout=PIPE)
	grep = subprocess.Popen(grep_command, stdin=docker_ls.stdout,
							stdout=PIPE, stderr=PIPE)
	docker_ls.stdout.close()
	out, err = grep.communicate()
	image = [word for word in out.decode('utf-8').split(" ") if len(word) > 0][2]

	# launch our docker container
	launch_command = ["docker", "run", "-d","-it", image]
	launch = subprocess.run(launch_command, stdout=PIPE, stderr=PIPE)
	
	# print(launch.stderr)
	container_id = launch.stdout.decode('utf-8')[:-1]

	if verbose:
		print("Launched container {}...".format(container_id[:12]))
	
	# copy the notebook files to the container
	copy_command = ["docker", "cp", notebook_path, container_id+ ":/home/notebooks/"]
	copy = subprocess.run(copy_command, stdout=PIPE, stderr=PIPE)
	
	# copy the test files to the container
	tests_command = ["docker", "cp", tests_dir, container_id+ ":/home/tests/"]
	tests = subprocess.run(tests_command, stdout=PIPE, stderr=PIPE)

	# copy the requirements file to the container
	if reqs:
		if verbose:
			print("Installing requirements in container {}...".format(container_id[:12]))
		reqs_command = ["docker", "cp", reqs, container_id+ ":/home"]
		requirements = subprocess.run(reqs_command, stdout=PIPE, stderr=PIPE)

		# install requirements
		install_command = ["docker", "exec", "-t", container_id, "pip3", "install", "-r", "/home/requirements.txt"]
		install = subprocess.run(install_command, stdout=PIPE, stderr=PIPE)

	if verbose:
		print("Grading {} in container {}...".format(("notebooks", "scripts")[scripts], container_id[:12]))
	
	# Now we have the notebooks in home/notebooks, we should tell the container to execute the grade command
	grade_command = ["docker", "exec", "-t", container_id, "python3", "-m", "otter.execute", "/home/notebooks"]

	# if we are grading scripts, add the --script flag
	if scripts:
		grade_command += ["--scripts"]

	grade = subprocess.run(grade_command, stdout=PIPE, stderr=PIPE)
	
	# Logging stdout/stderr with print statements
	print(grade.stdout.decode('utf-8'))
	print(grade.stderr.decode('utf-8'))

	# Logging stdout/stderr to file
	log_file = open("log_file_container_ {}.txt".format(id), "a+")
	log_file.write(grade.stdout.decode('utf-8'))
	log_file.write("\n")
	log_file.write(grade.stderr.decode('utf-8'))
	log_file.write("\n")
	log_file.close()

	all_commands = [launch, copy, tests, grade]
	try:
		all_commands += [requirements, install]
	except UnboundLocalError:
		pass

	try:
		for command in all_commands:
			if command.stderr.decode('utf-8') != '':
				raise Exception("Error running ", command, " failed with error: ", command.stderr.decode('utf-8'))

		if verbose:
			print("Copying grades from container {}...".format(container_id[:12]))

		# get the grades back from the container and read to date frame so we can merge later
		csv_command = ["docker", "cp", container_id+ ":/home/notebooks/grades.csv", "./grades"+id+".csv"]
		csv = subprocess.run(csv_command, stdout=PIPE, stderr=PIPE)
		df = pd.read_csv("./grades"+id+".csv")


		if unfiltered_pdfs or tag_filter or html_filter:
			mkdir_pdf_command = ["mkdir", "manual_submissions"]
			mkdir_pdf = subprocess.run(mkdir_pdf_command, stdout=PIPE, stderr=PIPE)
			
			# copy out manual submissions
			for pdf in df["manual"]:
				copy_cmd = ["docker", "cp", container_id + ":" + pdf, "./manual_submissions/" + re.search(r"\/([\w\-\_]*?\.pdf)", pdf)[1]]
				copy = subprocess.run(copy_cmd, stdout=PIPE, stderr=PIPE)

			def clean_pdf_filepaths(row):
				path = row["manual"]
				return re.sub(r"\/home\/notebooks", "manual_submissions", path)

			df["manual"] = df.apply(clean_pdf_filepaths, axis=1)

		if not no_kill:
			if verbose:
				print("Stopping container {}...".format(container_id[:12]))

			# cleanup the docker container
			stop_command = ["docker", "stop", container_id]
			stop = subprocess.run(stop_command, stdout=PIPE, stderr=PIPE)
			remove_command = ["docker", "rm", container_id]
			remove = subprocess.run(remove_command, stdout=PIPE, stderr=PIPE)

	except BaseException as e:
		if not no_kill:
			if verbose:
				print("Stopping container {}...".format(container_id[:12]))

			# cleanup the docker container
			stop_command = ["docker", "stop", container_id]
			stop = subprocess.run(stop_command, stdout=PIPE, stderr=PIPE)
			remove_command = ["docker", "rm", container_id]
			remove = subprocess.run(remove_command, stdout=PIPE, stderr=PIPE)
		
		raise e
	
	# check that no commands errored, if they did raise an informative exception
	all_commands = [launch, copy, tests, grade, csv, stop, remove]
	try:
		all_commands += [requirements, install]
	except UnboundLocalError:
		pass
	for command in all_commands:
		if command.stderr.decode('utf-8') != '':
			raise Exception("Error running ", command, " failed with error: ", command.stderr.decode('utf-8'))
  
	return df

def main(args):
    """
    Main function for running otter from the command line.
    """
    # Asserts that exactly one metadata flag is provided
    assert sum([meta != False for meta in [
        args.gradescope, 
        args.canvas, 
        args.json, 
        args.yaml
    ]]) == 1, "You must supply exactly one metadata flag (-g, -j, -y, -c)"

    # Asserts that either --pdf, --tag-filter, or --html-filter but not both provided
    assert sum([args.pdf, args.tag_filter, args.html_filter]) <= 1, "Cannot provide more than 1 PDF flag"

    # verbose flag
    verbose = args.verbose

    # Hand off metadata to parser
    if args.gradescope:
        meta_parser = GradescopeParser(args.path)
        if verbose:
            print("Found Gradescope metadata...")
    elif args.canvas:
        meta_parser = CanvasParser(args.path)
        if verbose:
            print("Found Canvas metadata...")
    elif args.json:
        meta_parser = JSONParser(os.path.join(args.json))
        if verbose:
            print("Found JSON metadata...")
    else:
        meta_parser = YAMLParser(os.path.join(args.yaml))
        if verbose:
            print("Found YAML metadata...")

    # check that reqs file is valid
    if not (os.path.exists(args.requirements) and os.path.isfile(args.requirements)):
        
        # if user-specified requirements not found, fail with AssertionError
        if args.requirements != "requirements.txt":
            assert False, "requirements file {} does not exist".format(args.requirements)

        # else just set to None and reqs are ignored
        args.requirements = None

    if verbose:
        print("Launching docker containers...")

    # Docker
    grades_dfs = launch_parallel_containers(args.tests_path, 
        args.path, 
        verbose=verbose, 
        unfiltered_pdfs=args.pdf, 
        tag_filter=args.tag_filter,
        html_filter=args.html_filter,
        reqs=args.requirements,
        num_containers=args.containers,
        image=args.image,
        scripts=args.scripts,
        no_kill=args.no_kill,
        output_path=args.output_path,
        debug=args.debug
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
    output_df.to_csv(os.path.join(args.output_path, "final_grades.csv"), index=False)
