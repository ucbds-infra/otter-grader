"""
Docker container management for Otter Grade
"""

import json
import subprocess
import re
import os
import shutil
import tempfile
import docker
import pandas as pd
import tarfile
import pkg_resources
import glob
import pickle

from subprocess import PIPE
from concurrent.futures import ThreadPoolExecutor, wait

from .metadata import GradescopeParser
from .utils import simple_tar, get_container_file, generate_hash, OTTER_DOCKER_IMAGE_TAG

from ..test_files import GradingResults


def build_image(zip_path, base_image, tag):
    """
    Creates a grading image based on the autograder zip file and attaches a tag.

    Args:
        zip_path (``str``): path to the autograder zip file
        base_image (``str``): base Docker image to build from
        tag (``str``): tag to be added when creating the image

    Returns:
        ``str``: the tag of the newly-build Docker image
    """
    image = OTTER_DOCKER_IMAGE_TAG + ":" + tag
    dockerfile = pkg_resources.resource_filename(__name__, "Dockerfile")
    build_out = subprocess.Popen(
        ["docker", "build","--build-arg", "ZIPPATH=" + zip_path, "--build-arg", "BASE_IMAGE=" + base_image,
         ".", "-f", dockerfile, "-t", image],
    )
    build_out.wait()
    return image

def launch_grade(zip_path, notebooks_dir, verbose=False, num_containers=None,
    scripts=False, no_kill=False, output_path="./", debug=False, zips=False, image="ucbdsinfra/otter-grader",
    meta_parser=None, pdfs=False):
    """
    Grades notebooks in parallel Docker containers

    This function runs ``num_containers`` Docker containers in parallel to grade the student submissions
    in ``notebooks_dir`` using the autograder configuration file at ``zip_path``. It can additionally 
    generate PDFs for the parts of the assignment needing manual grading.

    Args:
        zip_path(``str``): path to zip file used to set up container
        notebooks_dir (``str``): path to directory of student submissions to be graded
        verbose (``bool``, optional): whether status messages should be printed to the command line
        num_containers (``int``, optional): The number of parallel containers that will be run
        scripts (``bool``, optional): whether student submissions are Python scripts rather than
            Jupyter notebooks
        no_kill (``bool``, optional): whether the grading containers should be kept running after
            grading finishes
        output_path (``str``, optional): path at which to write grades CSVs copied from the container
        debug (``bool``, optional): whether to run grading in debug mode (prints grading STDOUT and STDERR
            from each container to the command line)
        zips (``bool``, optional): whether the submissions are zip files formatted from ``Notebook.export``
        image (``str``, optional): a base image to use for building Docker images
        meta_parser (object, optional): a metadata parser instance; one of the classes defined in
            ``otter.metadata``
        pdfs (``bool``, optional): whether to copy PDFs out of the containers

    Returns:
        ``list`` of ``pandas.core.frame.DataFrame``: the grades returned by each container spawned during
            grading
    """
    if not num_containers:
        num_containers = 4

    pool = ThreadPoolExecutor(num_containers)
    futures = []
    img = build_image(zip_path, image, generate_hash(zip_path))

    notebooks = glob.glob(os.path.join(notebooks_dir, "*.ipynb"))
    for nb_path in notebooks:
        futures += [pool.submit(grade_assignments,
            notebook_dir=nb_path,
            verbose=verbose,
            #TODO:check if path is not default for generate hash
            image=img,
            scripts=scripts,
            no_kill=no_kill,
            output_path=output_path,
            debug=debug,
            zips=zips,
            pdfs=pdfs
        )]

    # stop execution while containers are running
    finished_futures = wait(futures)

    # return list of dataframes
    return [df.result() for df in finished_futures[0]]


# TODO: these arguments need to be updated. replace notebooks_dir with the path to the notebook that
# this container will be grading
def grade_assignments(notebook_dir, image="ucbdsinfra/otter-grader", verbose=False,
    scripts=False, no_kill=False, output_path="./", debug=False, zips=False, pdfs=False):
    """
    Grades multiple submissions in a directory using a single docker container. If no PDF assignment is
    wanted, set all three PDF params (``unfiltered_pdfs``, ``tag_filter``, and ``html_filter``) to ``False``.

    Args:
        notebook_dir (``str``): path to directory of student submissions to be graded
        image (``str``, optional): a Docker image tag to be used for grading environment
        verbose (``bool``, optional): whether status messages should be printed to the command line
        scripts (``bool``, optional): whether student submissions are Python scripts rather than
            Jupyter notebooks
        no_kill (``bool``, optional): whether the grading containers should be kept running after
            grading finishes
        output_path (``str``, optional): path at which to write grades CSVs copied from the container
        debug (``bool``, False): whether to run grading in debug mode (prints grading STDOUT and STDERR
            from each container to the command line)
        zips (``bool``, False): whether the submissions are zip files formatted from ``Notebook.export``
        pdfs (``bool``, optional): whether to copy PDFs out of the containers

    Returns:
        ``pandas.core.frame.DataFrame``: A dataframe of file to grades information
    """
    # this is a fix for travis -- allows overriding docker client version
    if os.environ.get("OTTER_DOCKER_CLIENT_VERSION") is not None:
        client = docker.from_env(version=os.environ.get("OTTER_DOCKER_CLIENT_VERSION"))
    else:
        client = docker.from_env()
    container = client.containers.run(image, detach=True, tty=True)

    notebook_dir = os.path.abspath(notebook_dir)
    nb_name = os.path.splitext(os.path.split(notebook_dir)[1])[0]

    try:
        container_id = container.id[:12]

        if verbose:
            print(f"Launched container {container_id}...")

        # TODO: remember 1 subm per container, so we will use this content manager to put the
        #       notebook at /autograder/submission/{notebook name}.ipynb

        with simple_tar(notebook_dir) as tarf:
            container.put_archive("/autograder/submission", tarf)

        if verbose:
            print(f"Grading {('notebooks', 'scripts')[scripts]} in container {container_id}...")

        # Now we have the notebooks in home/notebooks, we should tell the container to execute the grade command...
        grade_command = ["/autograder/run_autograder"]

        exit_code, output = container.exec_run(grade_command)
        assert exit_code == 0, f"Container {container_id} failed with output:\n{output.decode('utf-8')}"

        if debug:
            print(output.decode("utf-8"))

        if verbose:
            print(f"Copying grades from container {container_id}...")

        # TODO: this needs to be updated to parse the JSON, found at path /autograder/results/results.json,
        #       into the existing CSV format so that this function returns a 1-row dataframe
        # get the grades back from the container and read to date frame so we can merge later
        
        # with get_container_file(container, "/home/notebooks/grades.csv") as f:
        #     df = pd.read_csv(f)
        
        #should be fixed @Edward
        with get_container_file(container, "/autograder/results/results.pkl") as f:
            scores = pickle.load(f)

        # TODO: wrangle results
        scores = scores.to_dict()
        scores = {t : [scores[t]["score"]] if type(scores[t]) == dict else scores[t] for t in scores}
        scores["file"] = os.path.split(notebook_dir)[1]
        df = pd.DataFrame(scores)

        # TODO: PDFs still need to work, so this code needs to be adapted to get the PDF of the notebook
        #       at path /autograder/submission/{notebook name}.pdf

        #not fixed yet @Edward

        if pdfs:
            with get_container_file(container, f"/autograder/submission/{nb_name}.pdf") as pdf_file:
                pdf_folder = os.path.join(os.path.abspath(output_path), "submission_pdfs")
                os.makedirs(pdf_folder, exist_ok=True)
            
                # # copy out manual submissions
                # for pdf in df["manual"]:
                local_pdf_path = os.path.join(pdf_folder, f"{nb_name}.pdf")
                with open(local_pdf_path, "wb+") as f:
                    f.write(pdf_file.read())
        
            # df["manual"] = df["manual"].str.replace("/home/notebooks", os.path.basename(pdf_folder))

        if not no_kill:
            if verbose:
                print(f"Stopping container {container_id}...")

            # cleanup the docker container
            container.stop()
            container.remove()

        client.close()

    except:

        # # delete the submission PDFs on failure
        # if pdfs and "pdf_folder" in locals():
        #     shutil.rmtree(pdf_folder)

        if not no_kill:
            if verbose:
                print(f"Stopping container {container_id}...")

            # cleanup the docker container
            container.stop()
            container.remove()

        client.close()

        raise

    return df
