"""
Docker container management for Otter Grade
"""

import subprocess
import re
import os
import shutil
import tempfile
import docker
import pandas as pd

from subprocess import PIPE
from concurrent.futures import ThreadPoolExecutor, wait

from .metadata import GradescopeParser
from .utils import simple_tar, get_container_file

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
    # this is a fix for travis -- allows overriding docker client version
    if os.environ.get("OTTER_DOCKER_CLIENT_VERSION") is not None:
        client = docker.from_env(version=os.environ.get("OTTER_DOCKER_CLIENT_VERSION"))
    else:
        client = docker.from_env()
    container = client.containers.run(image, detach=True, tty=True)

    try:        
        container_id = container.id[:12]

        if verbose:
            print(f"Launched container {container_id}...")

        with simple_tar(notebooks_dir) as tarf:
            container.put_archive("/home", tarf)
            container.exec_run(f"mv /home/{os.path.basename(notebooks_dir)} /home/notebooks")
        
        # copy the test files to the container
        if tests_dir is not None:
            with simple_tar(tests_dir) as tarf:
                container.put_archive("/home", tarf)
                container.exec_run(f"mv /home/{os.path.basename(tests_dir)} /home/tests")

        # copy the requirements file to the container
        if reqs:
            if verbose:
                print(f"Installing requirements in container {container_id}...")
            
            with simple_tar(reqs) as tarf:
                container.put_archive("/home", tarf)

            # install requirements
            exit_code, output = container.exec_run("pip install -r /home/requirements.txt")
            assert exit_code == 0, f"Container {container_id} failed to install requirements:\n{output.decode('utf-8')}"

            if debug:
                print(output.decode("utf-8"))

        if verbose:
            print(f"Grading {('notebooks', 'scripts')[scripts]} in container {container_id}...")
        
        # Now we have the notebooks in home/notebooks, we should tell the container to execute the grade command...
        grade_command = ["python3", "-m", "otter.grade", "/home/notebooks"]

        # if we want PDF output, add the necessary flag
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

        exit_code, output = container.exec_run(grade_command)
        assert exit_code == 0, f"Container {container_id} failed with output:\n{output.decode('utf-8')}"

        if debug:
            print(output.decode("utf-8"))
        
        if verbose:
            print(f"Copying grades from container {container_id}...")

        # get the grades back from the container and read to date frame so we can merge later
        with get_container_file(container, "/home/notebooks/grades.csv") as f:
            df = pd.read_csv(f)

        if pdfs:
            pdf_folder = os.path.join(os.path.abspath(output_path), "submission_pdfs")
            os.makedirs(pdf_folder, exist_ok=True)
            
            # copy out manual submissions
            for pdf in df["manual"]:
                local_pdf_path = os.path.join(pdf_folder, os.path.basename(pdf))
                with get_container_file(container, pdf) as pdf_file, open(local_pdf_path, "wb+") as f:
                    f.write(pdf_file.read())

            df["manual"] = df["manual"].str.replace("/home/notebooks", os.path.basename(pdf_folder))

        if not no_kill:
            if verbose:
                print(f"Stopping container {container_id}...")

            # cleanup the docker container
            container.stop()
            container.remove()
        
        client.close()

    except:

        # delete the submission PDFs on failure
        if pdfs and "pdf_folder" in locals():
            shutil.rmtree(pdf_folder)

        if not no_kill:
            if verbose:
                print(f"Stopping container {container_id}...")

            # cleanup the docker container
            container.stop()
            container.remove()
        
        client.close()
        
        raise
    
    return df
