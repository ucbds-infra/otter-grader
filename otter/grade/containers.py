"""
Docker container management for Otter Grade
"""

import glob
import os
import pickle
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, wait

import docker
import pandas as pd
import pkg_resources
from docker.errors import ImageNotFound

from .utils import generate_hash, OTTER_DOCKER_IMAGE_TAG


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
    if os.environ.get("OTTER_DOCKER_CLIENT_VERSION") is not None:
        client = docker.from_env(version=os.environ.get("OTTER_DOCKER_CLIENT_VERSION"))
    else:
        client = docker.from_env()
    try:
        client.images.get(image)
    except ImageNotFound:
        client.images.build(buildargs={
                                "ZIPPATH": zip_path,
                                "BASE_IMAGE": base_image
                            }, tag=image, dockerfile=dockerfile, path=".")
    return image


def launch_grade(zip_path, notebooks_dir, verbose=False, num_containers=None,
                 scripts=False, no_kill=False, output_path="./", debug=False, zips=False,
                 image="ucbdsinfra/otter-grader",
                 pdfs=False):
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

    if zips:
        pattern = "*.zip"
    else:
        pattern = "*.ipynb"

    notebooks = glob.glob(os.path.join(notebooks_dir, pattern))
    for nb_path in notebooks:
        futures += [
            pool.submit(
                grade_assignments,
                notebook_dir=nb_path,
                verbose=verbose,
                # TODO:check if path is not default for generate hash
                image=img,
                scripts=scripts,
                no_kill=no_kill,
                output_path=output_path,
                debug=debug,
                pdfs=pdfs,
            )
        ]

    # stop execution while containers are running
    finished_futures = wait(futures)

    # return list of dataframes
    return [df.result() for df in finished_futures[0]]


# TODO: these arguments need to be updated. replace notebooks_dir with the path to the notebook that
# this container will be grading
def grade_assignments(notebook_dir, image="ucbdsinfra/otter-grader", verbose=False,
                      scripts=False, no_kill=False, output_path="./", debug=False, pdfs=False):
    """
    Grades multiple submissions in a directory using a single docker container. If no PDF assignment is
    wanted, set all three PDF params (``unfiltered_pdfs``, ``tag_filter``, and ``html_filter``) to ``False``.

    Args:
        notebook_dir (``str``): path to the students submission to be graded
        image (``str``, optional): a Docker image tag to be used for grading environment
        verbose (``bool``, optional): whether status messages should be printed to the command line
        scripts (``bool``, optional): whether student submissions are Python scripts rather than
            Jupyter notebooks
        no_kill (``bool``, optional): whether the grading containers should be kept running after
            grading finishes
        output_path (``str``, optional): path at which to write grades CSVs copied from the container
        debug (``bool``, False): whether to run grading in debug mode (prints grading STDOUT and STDERR
            from each container to the command line)
        pdfs (``bool``, optional): whether to copy PDFs out of the containers

    Returns:
        ``pandas.core.frame.DataFrame``: A dataframe of file to grades information
    """
    # this is a fix for travis -- allows overriding docker client version
    if os.environ.get("OTTER_DOCKER_CLIENT_VERSION") is not None:
        client = docker.from_env(version=os.environ.get("OTTER_DOCKER_CLIENT_VERSION"))
    else:
        client = docker.from_env()

    fd, path = tempfile.mkstemp(suffix=".pkl")
    path_pdf = None
    if pdfs:
        _, path_pdf = tempfile.mkstemp(suffix=".pdf")
    try:

        nb_path = os.path.abspath(notebook_dir)
        nb_name = os.path.splitext(os.path.split(nb_path)[1])[0]

        volumes = {
            f"{nb_path}": {'bind': f"/autograder/submission/{os.path.split(nb_path)[1]}"},
            f"{path}": {'bind': "/autograder/results/results.pkl"}
        }
        if pdfs:
            volumes.update({f"{path_pdf}": {"bind": f"/autograder/submission/{nb_name}.pdf"}})
        container = client.containers.run(image, "/autograder/run_autograder", volumes=volumes,
                                          detach=True, tty=True)

        if verbose:
            print(f"Grading {('notebooks', 'scripts')[scripts]} in container {container.id}...")
        container.wait()
        if debug:
            print(container.logs(stderr=True, stdout=True).decode("utf-8"))
        if not no_kill:
            container.remove()

        with open(fd, "rb") as f:
            scores = pickle.load(f)

        # TODO: wrangle results
        scores = scores.to_dict()
        scores = {t: [scores[t]["score"]] if type(scores[t]) == dict else scores[t] for t in scores}
        scores["file"] = os.path.split(notebook_dir)[1]
        df = pd.DataFrame(scores)

        # TODO: PDFs still need to work, so this code needs to be adapted to get the PDF of the notebook
        #       at path /autograder/submission/{notebook name}.pdf

        # not fixed yet @Edward

        if pdfs:
            pdf_folder = os.path.join(os.path.abspath(output_path), "submission_pdfs")
            os.makedirs(pdf_folder, exist_ok=True)

            local_pdf_path = os.path.join(pdf_folder, f"{nb_name}.pdf")
            shutil.copy(path_pdf, local_pdf_path)
        client.close()
    except:
        raise
    finally:
        client.close()
        os.remove(path)
        if pdfs:
            os.remove(path_pdf)
    return df
