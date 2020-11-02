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
from hashlib import md5

from .metadata import GradescopeParser
from .utils import simple_tar, get_container_file, OTTER_DOCKER_IMAGE_TAG

from ..test_files import GradingResults

# TODO: docstring
def build_image(zip_path, base_image, tag):
    """Creates a new image based on the autograder zip file and attaches a tag.

    Args:
        zip_path (``str``): path to the autograder zip file
        tag (``str``): tag value to be added when creating the image


    Returns:
        ``str``: the string value of the newly built image
    """
    image = OTTER_DOCKER_IMAGE_TAG + ":" + tag
    dockerfile = pkg_resources.resource_filename(__name__, "Dockerfile")
    build_out = subprocess.Popen(
        ["docker", "build","--build-arg", "ZIPPATH=" + zip_path, "--build-arg", "BASE_IMAGE=" + base_image,
         ".", "-f", dockerfile, "-t", image],
    )
    build_out.wait()
    return image

# def new_create_container(test_folder_path, zip_hash):
#     dockerfile = BytesIO()
#     dockerfile_str = """
#         FROM gradescope/auto-builds
#         RUN apt-get update && apt-get install -y curl unzip dos2unix && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
#         RUN mkdir -p /autograder/source
#         ADD {test_folder_path} /tmp/autograder.zip
#         RUN unzip -d /autograder/source /tmp/autograder.zip
#         RUN cp /autograder/source/run_autograder /autograder/run_autograder
#         RUN dos2unix /autograder/run_autograder /autograder/source/setup.sh
#         RUN chmod +x /autograder/run_autograder
#         RUN apt-get update && bash /autograder/source/setup.sh && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
#         RUN mkdir -p /autograder/submission
#         RUN mkdir -p /autograder/results
#     """.format(test_folder_path=test_folder_path).encode("utf-8")
#
#     dockerfile.write(dockerfile_str)
#
#     # print(dockerfile_str)
#
#     # dockerfile_tar_info = tarfile.TarInfo("Dockerfile")
#     # dockerfile_tar_info.size = len(dockerfile_str)
#     #
#     # tar.addfile(dockerfile_tar_info, BytesIO(dockerfile_str))
#
#     client = docker.from_env()
#     client.images.build(fileobj=dockerfile,
#                         custom_context=False,
#                         # dockerfile="Dockerfile",
#                         tag=zip_hash,
#                         encoding="utf-8")
#     client.close()

def generate_hash(path):
    """Reads in a files content and returns a hash value string based
    on the file's content.

    Args:
        path (``str``): path to the file that will be read in and hashed

    Returns:
        ``str``: the hash value of the read in zip file
    """
    zip_hash = ""
    m = md5()
    with open(path, "rb") as f:
        data = f.read() #read file in chunk and call update on each chunk if file is large.
        m.update(data)
        zip_hash = m.hexdigest()
    return zip_hash

def launch_grade(gradescope_zip_path, notebooks_dir, verbose=False, num_containers=None,
    scripts=False, no_kill=False, output_path="./", debug=False, zips=False, image="ucbdsinfra/otter-grader",
    meta_parser=None, pdfs=False):
    """Grades notebooks in parallel docker containers

    This function runs ``num_containers`` docker containers in parallel to grade the student submissions
    in ``notebooks_dir`` using the tests in ``gradescope_zip_path``. It can additionally generate PDFs for the parts
    of the assignment needing manual grading.

    Args:
        gradescope_zip_path(``str``): path to zip file used to set up container
        notebooks_dir (``str``): path to directory of student submissions to be graded
        verbose (``bool``, optional): whether status messages should be printed to the command line
        num_containers (``int``, optional): The number of parallel containers that will be run
        scripts (``bool``, optional): whether student submissions are Python scripts rather than
            Jupyter notebooks
        no_kill (``bool``, optional): whether the grading containers should be kept running after
            grading finishes
        output_path (``str``, optional): path at which to write grades CSVs copied from the container
        debug (``bool``, False): whether to run grading in debug mode (prints grading STDOUT and STDERR
            from each container to the command line)
        zips (``bool``, False): whether the submissions are zip files formatted from ``Notebook.export``
        meta_parser (object, optional): a metadata parser instance; one of the classes defined in
            ``otter.metadata``

    Returns:
        ``list`` of ``pandas.core.frame.DataFrame``: the grades returned by each container spawned during
            grading
    """
    if not num_containers:
        num_containers = 4

    pool = ThreadPoolExecutor(num_containers)
    futures = []
    img =  build_image(gradescope_zip_path, image, generate_hash(gradescope_zip_path))

    # TODO: here we should be iterating through all notebooks in notebooks_dir, so that we call
    #       grade_assignments on the path to each notebook, and end up with several contains in the
    #       pool with num_containers being run at any given moment    
    # notebooks = []
    # for f in glob.glob(os.path.join(notebooks_dir, "*.ipynb")):
    #     notebooks.append(f)
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

# def launch_parallel_containers(tests_dir, notebooks_dir, verbose=False, pdfs=None, reqs=None,
#     num_containers=None, image="ucbdsinfra/otter-grader", scripts=False, no_kill=False, output_path="./",
#     debug=False, seed=None, zips=False, meta_parser=None):
#     """Grades notebooks in parallel docker containers
#
#     This function runs ``num_containers`` docker containers in parallel to grade the student submissions
#     in ``notebooks_dir`` using the tests in ``tests_dir``. It can additionally generate PDFs for the parts
#     of the assignment needing manual grading.
#
#     Args:
#         tests_dir (``str``): path to directory of tests
#         notebooks_dir (``str``): path to directory of student submissions to be graded
#         verbose (``bool``, optional): whether status messages should be printed to the command line
#         pdfs (``str``, optional): string indicating what type of PDF to generate; defaults to ``None``
#             indicating no PDFS but can be one of ``["unfiltered", "tags", "html"]`` corresponding to
#             the type of cell filtering to perform upon generation
#         reqs (``str``, optional): Path to requirements.txt file with non-standard packages needed
#         num_containers (``int``, optional): The number of parallel containers that will be run
#         image (``str``, optional): a docker image tag to be used for grading environment
#         scripts (``bool``, optional): whether student submissions are Python scripts rather than
#             Jupyter notebooks
#         no_kill (``bool``, optional): whether the grading containers should be kept running after
#             grading finishes
#         output_path (``str``, optional): path at which to write grades CSVs copied from the container
#         debug (``bool``, False): whether to run grading in debug mode (prints grading STDOUT and STDERR
#             from each container to the command line)
#         seed (``int``, optional): a random seed to use for intercell seeding during grading
#         zips (``bool``, False): whether the submissions are zip files formatted from ``Notebook.export``
#         meta_parser (object, optional): a metadata parser instance; one of the classes defined in
#             ``otter.metadata``
#
#     Returns:
#         ``list`` of ``pandas.core.frame.DataFrame``: the grades returned by each container spawned during
#             grading
#     """
#     if not num_containers:
#         num_containers = 4
#
#     # list all notebooks in the dir
#     dir_path = os.path.abspath(notebooks_dir)
#     file_extension = (".zip", ".py", ".ipynb")[[zips, scripts, True].index(True)]
#     notebooks = [os.path.join(dir_path, f) for f in os.listdir(dir_path) \
#         if os.path.isfile(os.path.join(dir_path, f)) and f.endswith(file_extension)]
#
#     # fix number of containers (overriding user input if necessary)
#     if len(notebooks) < num_containers:
#         num_containers = len(notebooks)
#
#     # # calculate number of notebooks per container
#     # num_per_group = int(len(notebooks) / num_containers)
#
#     try:
#         # create temp directories and add non-notebook files
#         dirs = [tempfile.mkdtemp() for _ in range(num_containers)]
#
#         # if GS export, get list of folder names to ignore when copying files
#         if isinstance(meta_parser, GradescopeParser):
#             ignore_folders = meta_parser.get_folders()
#         else:
#             ignore_folders = []
#
#         # copy all non-notebook files into each temp directory
#         for i in range(num_containers):
#             for file in os.listdir(dir_path):
#                 fp = os.path.join(dir_path, file)
#                 if os.path.isfile(fp) and os.path.splitext(fp)[1] != file_extension:
#                     shutil.copy(fp, dirs[i])
#                 elif os.path.isdir(fp) and fp not in ignore_folders:
#                     shutil.copytree(fp, os.path.join(dirs[i], file))
#
#         # copy notebooks in tmp directories
#         for k, v in enumerate(notebooks):
#             shutil.copy(v, dirs[k % num_containers])
#
#         # execute containers in parallel
#         pool = ThreadPoolExecutor(num_containers)
#         futures = []
#         for i in range(num_containers):
#             futures += [pool.submit(grade_assignments,
#                 tests_dir,
#                 dirs[i],
#                 str(i),
#                 verbose=verbose,
#                 pdfs=pdfs,
#                 # unfiltered_pdfs=unfiltered_pdfs,
#                 # tag_filter=tag_filter,
#                 # html_filter=html_filter,
#                 reqs=reqs,
#                 image=image,
#                 scripts=scripts,
#                 no_kill=no_kill,
#                 output_path=output_path,
#                 debug=debug,
#                 seed=seed,
#                 zips=zips
#             )]
#
#         # stop execution while containers are running
#         finished_futures = wait(futures)
#
#     # cleanup temp directories on failure
#     except:
#         for i in range(num_containers):
#             shutil.rmtree(dirs[i], ignore_errors=True)
#         raise
#
#     # cleanup temp directories
#     else:
#         for i in range(num_containers):
#             shutil.rmtree(dirs[i])
#
#     # return list of dataframes
#     return [df.result() for df in finished_futures[0]]

# TODO: these arguments need to be updated. replace notebooks_dir with the path to the notebook that
# this container will be grading
def grade_assignments(notebook_dir, image="ucbdsinfra/otter-grader", verbose=False,
    scripts=False, no_kill=False, output_path="./", debug=False, zips=False, pdfs=False):
    """
    Grades multiple submissions in a directory using a single docker container. If no PDF assignment is
    wanted, set all three PDF params (``unfiltered_pdfs``, ``tag_filter``, and ``html_filter``) to ``False``.

    Args:
        notebook_dir (``str``): path to directory of student submission to be graded
        image (``str``, optional): a docker image tag to be used for grading environment
        verbose (``bool``, optional): whether status messages should be printed to the command line
        scripts (``bool``, optional): whether student submissions are Python scripts rather than
            Jupyter notebooks
        no_kill (``bool``, optional): whether the grading containers should be kept running after
            grading finishes
        output_path (``str``, optional): path at which to write grades CSVs copied from the container
        debug (``bool``, False): whether to run grading in debug mode (prints grading STDOUT and STDERR
            from each container to the command line)
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

    notebook_dir = os.path.abspath(notebook_dir)
    nb_name = os.path.splitext(os.path.split(notebook_dir)[1])[0]

    try:
        container_id = container.id[:12]

        if verbose:
            print(f"Launched container {container_id}...")

        # TODO: remember 1 subm per container, so we will use this content manager to put the
        #       notebook at /autograder/submission/{notebook name}.ipynb

        # should be fixed @Edward
        with simple_tar(notebook_dir) as tarf:
            # container.put_archive("/home", tarf)
            container.put_archive("/autograder/submission", tarf)
            #exit_code, output = container.exec_run(f"mv /home/{os.path.basename(notebook_dir)} /home/notebooks")
            # exit_code, output = container.exec_run(f"mv /home/{os.path.basename(notebook_dir)} /autograder")
            # assert exit_code == 0, f"Container {container_id} failed with output:\n{output.decode('utf-8')}"

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
