########################################################
##### Docker Container Management for Otter-Grader #####
########################################################

import subprocess
import re
import os
import shutil
import tempfile
import pandas as pd

from subprocess import PIPE
from concurrent.futures import ThreadPoolExecutor, wait

from .metadata import GradescopeParser

def launch_parallel_containers(tests_dir, notebooks_dir, verbose=False, pdfs=None, reqs=None, 
    num_containers=None, image="ucbdsinfra/otter-grader", scripts=False, no_kill=False, output_path="./", 
    debug=False, seed=None, zips=False, meta_parser=None):
    """Grades notebooks in parallel docker containers

    This function runs ``num_containers`` docker containers in parallel to grade the student submissions
    in ``notebooks_dir`` using the tests in ``tests_dir``. It can additionally generate PDFs for the parts
    of the assignment needing manual grading. 

    Args:
        tests_dir (``str``): path to directory of tests
        notebooks_dir (``str``): path to directory of student submissions to be graded
        verbose (``bool``, optional): whether status messages should be printed to the command line
        pdfs (``str``, optional): string indicating what type of PDF to generate; defaults to ``None``
            indicating no PDFS but can be one of ``["unfiltered", "tags", "html"]`` corresponding to
            the type of cell filtering to perform upon generation
        reqs (``str``, optional): Path to requirements.txt file with non-standard packages needed
        num_containers (``int``, optional): The number of parallel containers that will be run
        image (``str``, optional): a docker image tag to be used for grading environment
        scripts (``bool``, optional): whether student submissions are Python scripts rather than
            Jupyter notebooks
        no_kill (``bool``, optional): whether the grading containers should be kept running after
            grading finishes
        output_path (``str``, optional): path at which to write grades CSVs copied from the container
        debug (``bool``, False): whether to run grading in debug mode (prints grading STDOUT and STDERR 
            from each container to the command line)
        seed (``int``, optional): a random seed to use for intercell seeding during grading
        zips (``bool``, False): whether the submissions are zip files formatted from ``Notebook.export``
        meta_parser (object, optional): a metadata parser instance; one of the classes defined in
            ``otter.metadata``

    Returns:
        ``list`` of ``pandas.core.frame.DataFrame``: the grades returned by each container spawned during
            grading
    """
    if not num_containers:
        num_containers = 4

    # list all notebooks in the dir
    dir_path = os.path.abspath(notebooks_dir)
    file_extension = (".zip", ".py", ".ipynb")[[zips, scripts, True].index(True)]
    notebooks = [os.path.join(dir_path, f) for f in os.listdir(dir_path) \
        if os.path.isfile(os.path.join(dir_path, f)) and f.endswith(file_extension)]

    # fix number of containers (overriding user input if necessary)
    if len(notebooks) < num_containers:
        num_containers = len(notebooks)

    # # calculate number of notebooks per container
    # num_per_group = int(len(notebooks) / num_containers)

    try:
        # create temp directories and add non-notebook files
        dirs = [tempfile.mkdtemp() for _ in range(num_containers)]

        # if GS export, get list of folder names to ignore when copying files
        if isinstance(meta_parser, GradescopeParser):
            ignore_folders = meta_parser.get_folders()
        else:
            ignore_folders = []

        # copy all non-notebook files into each temp directory
        for i in range(num_containers):
            for file in os.listdir(dir_path):
                fp = os.path.join(dir_path, file)
                if os.path.isfile(fp) and os.path.splitext(fp)[1] != file_extension:
                    shutil.copy(fp, dirs[i])
                elif os.path.isdir(fp) and fp not in ignore_folders:                    
                    shutil.copytree(fp, os.path.join(dirs[i], file))

        # copy notebooks in tmp directories
        for k, v in enumerate(notebooks):
            shutil.copy(v, dirs[k % num_containers])

        # execute containers in parallel
        pool = ThreadPoolExecutor(num_containers)
        futures = []
        for i in range(num_containers):
            futures += [pool.submit(grade_assignments, 
                tests_dir, 
                dirs[i], 
                str(i), 
                verbose=verbose, 
                pdfs=pdfs,
                # unfiltered_pdfs=unfiltered_pdfs, 
                # tag_filter=tag_filter,
                # html_filter=html_filter,
                reqs=reqs,
                image=image,
                scripts=scripts,
                no_kill=no_kill,
                output_path=output_path,
                debug=debug,
                seed=seed,
                zips=zips
            )]

        # stop execution while containers are running
        finished_futures = wait(futures)
    
    # cleanup temp directories on failure
    except:
        for i in range(num_containers):
            shutil.rmtree(dirs[i], ignore_errors=True)
        raise
    
    # cleanup temp directories
    else:
        for i in range(num_containers):
            shutil.rmtree(dirs[i])

    # return list of dataframes
    return [df.result() for df in finished_futures[0]]

def grade_assignments(tests_dir, notebooks_dir, id, image="ucbdsinfra/otter-grader", verbose=False, 
    pdfs=False, reqs=None, scripts=False, no_kill=False, output_path="./", debug=False, seed=None, zips=False):
    """
    Grades multiple assignments in a directory using a single docker container. If no PDF assignment is 
    wanted, set all three PDF params (``unfiltered_pdfs``, ``tag_filter``, and ``html_filter``) to ``False``.

    Args:
        tests_dir (``str``): path to directory of tests
        notebooks_dir (``str``): path to directory of student submissions to be graded
        id (``int``): grading container index
        image (``str``, optional): a docker image tag to be used for grading environment
        verbose (``bool``, optional): whether status messages should be printed to the command line
        pdfs (``str``, optional): string indicating what type of PDF to generate; defaults to ``None``
            indicating no PDFS but can be one of ``["unfiltered", "tags", "html"]`` corresponding to
            the type of cell filtering to perform upon generation
        reqs (``str``, optional): Path to requirements.txt file with non-standard packages needed
        scripts (``bool``, optional): whether student submissions are Python scripts rather than
            Jupyter notebooks
        no_kill (``bool``, optional): whether the grading containers should be kept running after
            grading finishes
        output_path (``str``, optional): path at which to write grades CSVs copied from the container
        debug (``bool``, False): whether to run grading in debug mode (prints grading STDOUT and STDERR 
            from each container to the command line)
        seed (``int``, optional): a random seed to use for intercell seeding during grading
        zips (``bool``, False): whether the submissions are zip files formatted from ``Notebook.export``

    Returns:
        ``pandas.core.frame.DataFrame``: A dataframe of file to grades information
    """
    # launch our docker conainer
    launch_command = ["docker", "run", "-d","-it", image]
    launch = subprocess.run(launch_command, stdout=PIPE, stderr=PIPE)
    
    # print(launch.stderr)
    container_id = launch.stdout.decode('utf-8')[:-1]

    if verbose:
        print(f"Launched container {container_id[:12]}...")
    
    # copy the notebook files to the container
    copy_command = ["docker", "cp", notebooks_dir, f"{container_id}:/home/notebooks/"]
    copy = subprocess.run(copy_command, stdout=PIPE, stderr=PIPE)
    
    # copy the test files to the container
    if tests_dir is not None:
        tests_command = ["docker", "cp", tests_dir, f"{container_id}:/home/tests/"]
        tests = subprocess.run(tests_command, stdout=PIPE, stderr=PIPE)

    # copy the requirements file to the container
    if reqs:
        if verbose:
            print(f"Installing requirements in container {container_id[:12]}...")
        reqs_command = ["docker", "cp", reqs, f"{container_id}:/home"]
        requirements = subprocess.run(reqs_command, stdout=PIPE, stderr=PIPE)

        # install requirements
        install_command = [
            "docker", "exec", "-t", container_id, "pip3", "install", "-r", "/home/requirements.txt"
        ]
        install = subprocess.run(install_command, stdout=PIPE, stderr=PIPE)

    if verbose:
        print(f"Grading {('notebooks', 'scripts')[scripts]} in container {container_id[:12]}...")
    
    # Now we have the notebooks in home/notebooks, we should tell the container to execute the 
    # grade command...
    grade_command = [
        "docker", "exec", "-t", container_id, "python3", "-m", "otter", "/home/notebooks"
    ]

    # if we want PDF output, add the necessary flag
    # if unfiltered_pdfs:
    #     grade_command += ["--pdf"]
    # elif tag_filter:
    #     grade_command += ["--pdf", "tags"]
    # elif html_filter:
    #     grade_command += ["--pdf", "html"]
    if pdfs:
        grade_command += ["--pdf", pdfs]
    
    # seed
    if seed is not None:
        grade_command += ["--seed", str(seed)]

    # if we are grading scripts, add the --script flag
    if scripts:
        grade_command += ["--scripts"]
    
    if debug:
        grade_command += ["--verbose"]

    if zips:
        grade_command += ["--zips"]

    grade = subprocess.run(grade_command, stdout=PIPE, stderr=PIPE)
    
    if debug:
        print(grade.stdout.decode("utf-8"))
        print(grade.stderr.decode("utf-8"))

    all_commands = [launch, copy, grade]
    try: 
        all_commands += [tests]
    except UnboundLocalError:
        pass
    try:
        all_commands += [requirements, install]
    except UnboundLocalError:
        pass

    try:
        for command in all_commands:
            if command.stderr.decode('utf-8') != '':
                raise Exception(f"Error running {command}; failed with error:\n{command.stderr.decode('utf-8')}")

        if verbose:
            print(f"Copying grades from container {container_id[:12]}...")

        # get the grades back from the container and read to date frame so we can merge later
        csv_command = [
            "docker", "cp", f"{container_id}:/home/notebooks/grades.csv", f"./grades{id}.csv"
        ]
        csv = subprocess.run(csv_command, stdout=PIPE, stderr=PIPE)
        df = pd.read_csv(f"./grades{id}.csv")

        if pdfs:
            pdf_folder = os.path.join(os.path.abspath(output_path), "submission_pdfs")
            os.makedirs(pdf_folder, exist_ok=True)
            
            # copy out manual submissions
            for pdf in df["manual"]:
                copy_cmd = [
                    "docker", "cp", f"{container_id}:{pdf}", os.path.join(pdf_folder, os.path.basename(pdf))
                ]
                copy = subprocess.run(copy_cmd, stdout=PIPE, stderr=PIPE)

            df["manual"] = df["manual"].str.replace("/home/notebooks", "submission_pdfs")
        
        # delete the file we just read
        csv_cleanup_command = ["rm", f"./grades{id}.csv"]
        csv_cleanup = subprocess.run(csv_cleanup_command, stdout=PIPE, stderr=PIPE)

        if not no_kill:
            if verbose:
                print(f"Stopping container {container_id[:12]}...")

            # cleanup the docker container
            stop_command = ["docker", "stop", container_id]
            stop = subprocess.run(stop_command, stdout=PIPE, stderr=PIPE)
            remove_command = ["docker", "rm", container_id]
            remove = subprocess.run(remove_command, stdout=PIPE, stderr=PIPE)

    except:
        # delete the file we just read
        csv_cleanup_command = ["rm", f"./grades{id}.csv"]
        csv_cleanup = subprocess.run(csv_cleanup_command, stdout=PIPE, stderr=PIPE)

        # delete the submission PDFs on failure
        if pdfs:
            csv_cleanup_command = ["rm", "-rf", os.path.join(output_path, "submission_pdfs")]
            csv_cleanup = subprocess.run(csv_cleanup_command, stdout=PIPE, stderr=PIPE)

        if not no_kill:
            if verbose:
                print(f"Stopping container {container_id[:12]}...")

            # cleanup the docker container
            stop_command = ["docker", "stop", container_id]
            stop = subprocess.run(stop_command, stdout=PIPE, stderr=PIPE)
            remove_command = ["docker", "rm", container_id]
            remove = subprocess.run(remove_command, stdout=PIPE, stderr=PIPE)
        
        raise
    
    # check that no commands errored, if they did rais an informative exception
    all_commands = [launch, copy, grade, csv, csv_cleanup]

    try:
        all_commands += [stop, remove]
    except UnboundLocalError:
        pass

    try:
        all_commands += [tests]
    except UnboundLocalError:
        pass

    try:
        all_commands += [requirements, install]
    except UnboundLocalError:
        pass

    for command in all_commands:
        for command in all_commands:
            if command.stderr.decode('utf-8') != '':
                raise Exception(f"Error running {command}; failed with error:\n{command.stderr.decode('utf-8')}")
    
    return df
