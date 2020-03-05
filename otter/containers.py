########################################################
##### Docker Container Management for Otter-Grader #####
########################################################

import pandas as pd
import subprocess
from subprocess import PIPE
import json
import re
from concurrent.futures import ThreadPoolExecutor, wait
import os
import shutil

def launch_parallel_containers(
    tests_dir, notebooks_dir, verbose=False, unfiltered_pdfs=False, tag_filter=False, 
    html_filter=False, reqs=None, num_containers=None, image="ucbdsinfra/otter-grader", 
    scripts=False, no_kill=False):
    """Grades notebooks in parallel docker containers

    This function runs NUM_CONTAINERS docker containers in parallel to grade the student submissions
    in NOTEBOOKS_DIR using the tests in TESTS_DIR. It can additionally generate PDFs for the parts
    of the assignment needing manual grading. 

    Args:
        tests_dir (str): Path to directory with ok-style tests
        notebooks_dir (str): Path to student submissions to be graded against provided tests
        verbose (bool, optional): Set true to see logs of grade_assignments function as it runs
        unfiltered_pdfs (bool, optional): Set true to create PDF of entire ipython notebook
        tag_filter (bool, optional): Set true if notebook cells should be filtered by tag
        html_filter (bool, optional): Set true if notebook cells should be filtered by comments
        reqs (str, optional): Path to requirements.txt file with non-standard packages needed
        num_containers (int, optional): The number of parallel containers that will be run
        image (str, optional): Name of docker image used for grading environment
        scripts (bool, optional): Set true if student submissions are .py instead of .ipynb
        no_kill (bool, optional): Set true to keep containers running after function terminates

    Returns:
        list: List of all dataframes which result from each container's execution
    """
    if not num_containers:
        num_containers = 4

    # list all notebooks in the dir
    dir_path = os.path.abspath(notebooks_dir)
    file_extension = (".py", ".ipynb")[not scripts]
    notebooks = [os.path.join(dir_path, f) for f in os.listdir(dir_path) \
        if os.path.isfile(os.path.join(dir_path, f)) and f.endswith(file_extension)]

    # fix number of containers (overriding user input if necessary)
    if len(notebooks) < num_containers:
        num_containers = len(notebooks)

    # calculate number of notebooks per container
    num_per_group = int(len(notebooks) / num_containers)

    # create tmp directories and add non-notebook files
    for i in range(num_containers):
        os.mkdir(os.path.join(dir_path, "tmp{}".format(i)))

        # copy all non-notebook files into each tmp directory
        for file in os.listdir(dir_path):
            if os.path.isfile(os.path.join(dir_path, file)) and not file.endswith(file_extension):
                shutil.copy(os.path.join(dir_path, file), os.path.join(dir_path, "tmp{}".format(i)))

    # copy notebooks in tmp directories
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
            unfiltered_pdfs=unfiltered_pdfs, 
            tag_filter=tag_filter,
            html_filter=html_filter,
            reqs=reqs,
            image=image,
            scripts=scripts,
            no_kill=no_kill
        )]

    # stop execution while containers are running
    finished_futures = wait(futures)

    # clean up tmp directories
    for i in range(num_containers):
        shutil.rmtree(os.path.join(dir_path, "tmp{}".format(i)))

    # return list of dataframes
    return [df.result() for df in finished_futures[0]]


def grade_assignments(tests_dir, notebooks_dir, id, image="ucbdsinfra/otter-grader", verbose=False, 
unfiltered_pdfs=False, tag_filter=False, html_filter=False, reqs=None, 
scripts=False, no_kill=False):
    """
    Grades multiple assignments in a directory using a single docker container. 

    If no PDF assignment is wanted, set all three PDF params (unfiltered_pdfs, tag_filter, 
    html_filter) to false. Also, list any non-standard package requirements in a requirements.txt 
    file. This function can grade files with .py or .ipynb extensions (use scripts=True for .py). 

    Args:
        tests_dir (str, optional): Directory of test files
        notebooks_dir (str, optional): Directory of notebooks to grade
        id (str, optional): Id of this function for mc use
        image (str, optional): Docker image to do grading in
        verbose (bool, optional): Whether function should print information about various steps
        unfiltered_pdfs (bool, optional): Set true if no filtering needed (generate pdf of whole nb)
        tag_filter (bool, optional): Set true if notebook cells should be filtered by tag
        html_filter (bool, optional): Set true if notebook cells should be filtered by comments
        reqs (str, optional): Path to pip-style requirements.txt file 
        scripts (bool, optional): Set true if we are grading .py files instead of ipython notebooks
        no_kill (bool, optional: Set true to keep containers running after function terminates

    Returns:
        pandas.core.frame.DataFrame: A dataframe of file to grades information
    """
    # launch our docker conainer
    launch_command = ["docker", "run", "-d","-it", image]
    launch = subprocess.run(launch_command, stdout=PIPE, stderr=PIPE)
    
    # print(launch.stderr)
    container_id = launch.stdout.decode('utf-8')[:-1]

    if verbose:
        print("Launched container {}...".format(container_id[:12]))
    
    # copy the notebook files to the container
    copy_command = ["docker", "cp", notebooks_dir, container_id+ ":/home/notebooks/"]
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
        install_command = ["docker", "exec", "-t", container_id, "pip3", "install", "-r", \
            "/home/requirements.txt"]
        install = subprocess.run(install_command, stdout=PIPE, stderr=PIPE)

    if verbose:
        print("Grading {} in container {}...".format(("notebooks", "scripts")[scripts], \
            container_id[:12]))
    
    # Now we have the notebooks in home/notebooks, we should tell the container 
    # to execute the grade command....
    # grade_command = ["docker", "exec", "-t", container_id, "python3", "/home/grade.py", 
    # "/home/notebooks"]
    grade_command = ["docker", "exec", "-t", container_id, "python3", "-m", "otter.grade", \
        "/home/notebooks"]

    # if we want PDF output, add the necessary flag
    if unfiltered_pdfs:
        grade_command += ["--pdf"]
    if tag_filter:
        grade_command += ["--tag-filter"]
    if html_filter:
        grade_command += ["--html-filter"]

    # if we are grading scripts, add the --script flag
    if scripts:
        grade_command += ["--scripts"]

    grade = subprocess.run(grade_command, stdout=PIPE, stderr=PIPE)
    # print(grade.stdout.decode("utf-8"))
    # print(grade.stderr.decode("utf-8"))

    all_commands = [launch, copy, tests, grade]
    try:
        all_commands += [requirements, install]
    except UnboundLocalError:
        pass

    try:
        for command in all_commands:
            if command.stderr.decode('utf-8') != '':
                raise Exception("Error running ", command, " failed with error: ", \
                    command.stderr.decode('utf-8'))

        if verbose:
            print("Copying grades from container {}...".format(container_id[:12]))

        # get the grades back from the container and read to date frame so we can merge later
        csv_command = ["docker", "cp", container_id+ ":/home/notebooks/grades.csv", \
            "./grades"+id+".csv"]
        csv = subprocess.run(csv_command, stdout=PIPE, stderr=PIPE)
        df = pd.read_csv("./grades"+id+".csv")

        if unfiltered_pdfs or tag_filter or html_filter:
            mkdir_pdf_command = ["mkdir", "manual_submissions"]
            mkdir_pdf = subprocess.run(mkdir_pdf_command, stdout=PIPE, stderr=PIPE)
            
            # copy out manual submissions
            for pdf in df["manual"]:
                copy_cmd = ["docker", "cp", container_id + ":" + pdf, "./manual_submissions/" \
                    + re.search(r"\/([\w\-\_]*?\.pdf)", pdf)[1]]
                copy = subprocess.run(copy_cmd, stdout=PIPE, stderr=PIPE)

            def clean_pdf_filepaths(row):
                """
                Generates a clean filepath for a PDF

                Replaces occurrences of '/home/notebooks' with 'manual_submission' in the
                path. 
                
                Arguments:
                    row (pandas.core.series.Series): row of a dataframe
                
                Returns:
                    str: cleaned PDF filepath
                """
                path = row["manual"]
                return re.sub(r"\/home\/notebooks", "manual_submissions", path)

            df["manual"] = df.apply(clean_pdf_filepaths, axis=1)
        
        # delete the file we just read
        csv_cleanup_command = ["rm", "./grades"+id+".csv"]
        csv_cleanup = subprocess.run(csv_cleanup_command, stdout=PIPE, stderr=PIPE)

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
    
    # check that no commands errored, if they did rais an informative exception
    all_commands = [launch, copy, tests, grade, csv, csv_cleanup, stop, remove]
    try:
        all_commands += [requirements, install]
    except UnboundLocalError:
        pass
    for command in all_commands:
        if command.stderr.decode('utf-8') != '':
            raise Exception("Error running ", command, " failed with error: ", \
                command.stderr.decode('utf-8'))
    return df
