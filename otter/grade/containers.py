"""Docker container management for Otter Grade"""

import os
import pandas as pd
import pkg_resources
import shutil
import tempfile
import zipfile

from concurrent.futures import ThreadPoolExecutor, wait
from python_on_whales import docker
from textwrap import indent
from typing import List, Optional

from .utils import OTTER_DOCKER_IMAGE_NAME

from ..utils import loggers


DOCKER_PLATFORM = "linux/amd64"
LOGGER = loggers.get_logger(__name__)

# Set this to true in a test file to indicate that one of Otter's unit tests is being run; this
# will tell Otter to copy the working directory (the Otter repo) into the container and install it
# so that the version of Otter installed in the container has all local edits.
_TESTING = False


def build_image(ag_zip_path: str, base_image: str, tag: str):
    """
    Creates a grading image based on the autograder zip file and attaches a tag.

    Args:
        ag_zip_path (``str``): path to the autograder zip file
        base_image (``str``): base Docker image to build from
        tag (``str``): tag to be added when creating the image

    Returns:
        ``str``: the tag of the newly-build Docker image
    """
    image = OTTER_DOCKER_IMAGE_NAME + ":" + tag
    dockerfile_path = pkg_resources.resource_filename(__name__, "Dockerfile")

    LOGGER.info(f"Building image using {base_image} as base image")

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(ag_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # build_args = {"BASE_IMAGE": base_image}
        # if _TESTING:
        #     build_args["BUILD_ENV"] = "test"

        docker.build(
            temp_dir,
            build_args={"BASE_IMAGE": base_image},
            tags=[image],
            file=dockerfile_path,
            load=True,
            platforms=[DOCKER_PLATFORM],
        )

    return image


def launch_containers(
    ag_zip_path: str,
    submission_paths: List[str],
    num_containers: int,
    base_image: str,
    tag: str,
    **kwargs,
):
    """
    Grade submissions in parallel Docker containers.

    This function runs ``num_containers`` Docker containers in parallel to grade the student
    submissions in ``submissions_dir`` using the autograder configuration file at ``ag_zip_path``. 
    If indicated, it copies the PDFs generated of the submissions out of their containers.

    Args:
        ag_zip_path (``str``): path to zip file used to set up container
        submission_paths (``str``): paths of submissions to be graded
        num_containers (``int``, optional): number of containers to run in parallel
        image (``str``, optional): a base image to use for building Docker images
        **kwargs: additional kwargs passed to ``grade_submission``

    Returns:
        ``list[pandas.core.frame.DataFrame]``: the grades returned by each container spawned
            during grading
    """
    pool = ThreadPoolExecutor(num_containers)
    futures = []
    image = build_image(ag_zip_path, base_image, tag)

    for subm_path in submission_paths:
        futures += [
            pool.submit(grade_submission, submission_path=subm_path, image=image, **kwargs)
        ]

    # stop execution while containers are running
    finished_futures = wait(futures)

    # return list of dataframes
    return [df.result() for df in finished_futures[0]]


def grade_submission(
    submission_path: str,
    image: str,
    no_kill: bool = False,
    pdf_dir: Optional[str] = None,
    timeout: Optional[int] = None,
    network: bool = True,
):
    """
    Grade a submission in a Docker container.

    Args:
        submission_path (``str``): path to the submission to be graded
        image (``str``): a Docker image tag to be used for grading environment
        no_kill (``bool``, optional): whether the grading containers should be kept running after
            grading finishes
        pdf_dir (``str``, optional): a directory in which to put the notebook PDF, if applicable
        timeout (``int``): timeout in seconds for each container
        network (``bool``): whether to enable networking in the containers

    Returns:
        ``pandas.core.frame.DataFrame``: A dataframe of file to grades information
    """
    import dill

    temp_subm_file, temp_subm_path = tempfile.mkstemp()
    shutil.copyfile(submission_path, temp_subm_path)

    results_file, results_path = tempfile.mkstemp(suffix=".pkl")
    pdf_path = None
    if pdf_dir:
        pdf_file, pdf_path = tempfile.mkstemp(suffix=".pdf")

    try:
        nb_basename = os.path.basename(submission_path)
        nb_name = os.path.splitext(nb_basename)[0]

        volumes = [
            (temp_subm_path, f"/autograder/submission/{nb_basename}"),
            (results_path, "/autograder/results/results.pkl")
        ]
        if pdf_dir:
            volumes.append((pdf_path, f"/autograder/submission/{nb_name}.pdf"))

        run_kwargs = {}
        if network is not None and not network:
            run_kwargs['networks'] = 'none'

        container = docker.container.run(
            image,
            command=["/autograder/run_autograder"],
            volumes=volumes,
            detach=True,
            platform=DOCKER_PLATFORM,
            **run_kwargs,
        )

        if timeout:
            import threading

            def kill_container():
                docker.container.kill(container)

            timer = threading.Timer(timeout, kill_container)
            timer.start()

        container_id = container.id[:12]
        LOGGER.info(f"Grading {submission_path} in container {container_id}...")

        exit = docker.container.wait(container)

        if timeout:
            timer.cancel()

        logs = docker.container.logs(container)
        LOGGER.debug(f"Container {container_id} logs:\n{indent(logs, '    ')}")

        if not no_kill:
            container.remove()

        if exit != 0:
            raise Exception(
                f"Executing '{submission_path}' in docker container failed! Exit code: {exit}")

        with open(results_path, "rb") as f:
            scores = dill.load(f)

        scores_dict = scores.to_dict()
        scores_dict["percent_correct"] = scores.total / scores.possible

        scores_dict = {t: [scores_dict[t]["score"]] if type(scores_dict[t]) == dict else scores_dict[t] for t in scores_dict}
        scores_dict["file"] = submission_path
        df = pd.DataFrame(scores_dict)

        if pdf_dir:
            os.makedirs(pdf_dir, exist_ok=True)

            local_pdf_path = os.path.join(pdf_dir, f"{nb_name}.pdf")
            shutil.copy(pdf_path, local_pdf_path)

    finally:
        os.close(results_file)
        os.remove(results_path)
        os.close(temp_subm_file)
        os.remove(temp_subm_path)
        if pdf_dir:
            os.close(pdf_file)
            os.remove(pdf_path)

    return df
