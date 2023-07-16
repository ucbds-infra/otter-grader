"""Docker container management for Otter Grade"""

import json
import os
import pandas as pd
import pathlib
import pkg_resources
import shutil
import tempfile
import zipfile

from concurrent.futures import ThreadPoolExecutor, wait
from python_on_whales import docker
from textwrap import indent
from typing import List, Optional

from .utils import OTTER_DOCKER_IMAGE_NAME

from ..run.run_autograder.autograder_config import AutograderConfig
from ..utils import loggers


LOGGER = loggers.get_logger(__name__)


def build_image(ag_zip_path: str, base_image: str, tag: str, config: AutograderConfig):
    """
    Creates a grading image based on the autograder zip file and attaches a tag.

    Args:
        ag_zip_path (``str``): path to the autograder zip file
        base_image (``str``): base Docker image to build from
        tag (``str``): tag to be added when creating the image
        config (``otter.run.run_autograder.autograder_config.AutograderConfig``): config overrides
            for the autograder

    Returns:
        ``str``: the tag of the newly-build Docker image
    """
    image = OTTER_DOCKER_IMAGE_NAME + ":" + tag
    dockerfile_path = pkg_resources.resource_filename(__name__, "Dockerfile")

    LOGGER.info(f"Building image using {base_image} as base image")

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(ag_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Update the otter_config.json file from the autograder zip with the provided config
        # overrides.
        config_path = pathlib.Path(temp_dir) / "otter_config.json"
        old_config = AutograderConfig()
        if config_path.exists():
            old_config = AutograderConfig(json.loads(config_path.read_text("utf-8")))

        old_config.update(config.get_user_config())
        config_path.write_text(json.dumps(old_config.get_user_config()))

        docker.build(
            temp_dir,
            build_args={"BASE_IMAGE": base_image},
            tags=[image],
            file=dockerfile_path,
            load=True,
        )

    return image


def launch_containers(
    ag_zip_path: str,
    submission_paths: List[str],
    num_containers: int,
    base_image: str,
    tag: str,
    config: AutograderConfig,
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
        num_containers (``int``): number of containers to run in parallel
        base_image (``str``): the name of a base image to use for building Docker images
        tag (``str``): a tag to use for the ``otter-grade`` image created for this assignment
        config (``otter.run.run_autograder.autograder_config.AutograderConfig``): config overrides
            for the autograder
        **kwargs: additional kwargs passed to ``grade_submission``

    Returns:
        ``list[pandas.core.frame.DataFrame]``: the grades returned by each container spawned
            during grading
    """
    pool = ThreadPoolExecutor(num_containers)
    futures = []
    image = build_image(ag_zip_path, base_image, tag, config)

    for subm_path in submission_paths:
        futures += [pool.submit(
            grade_submission,
            submission_path=subm_path,
            image=image,
            # config=config,
            **kwargs,
        )]

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
        no_kill (``bool``): whether the grading containers should be kept running after
            grading finishes
        pdf_dir (``str``, optional): a directory in which to put the notebook PDF, if applicable
        timeout (``int``, optional): timeout in seconds for each container
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

        args = {}
        if network is not None and not network:
            args['networks'] = 'none'

        container = docker.container.create(image, command=["/autograder/run_autograder"], **args)

        for local_path, container_path in volumes:
            docker.container.copy(local_path, (container, container_path))

        docker.container.start(container)

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

        # Close our file handles since docker cp will delete the original file when performing the
        # copy.
        os.close(temp_subm_file)
        os.close(results_file)
        if pdf_path:
            os.close(pdf_file)

        for local_path, container_path in volumes:
            docker.container.copy((container, container_path), local_path)

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
        os.remove(results_path)
        os.remove(temp_subm_path)

    return df
