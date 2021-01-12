"""
Utilities for Otter Grade
"""

import tempfile
import tarfile
import os
import docker
import pandas as pd

from contextlib import contextmanager
from hashlib import md5

OTTER_DOCKER_IMAGE_TAG = "otter-grade"

@contextmanager
def simple_tar(path):
    """
    Context manager that takes a file at ``path`` and creates a temporary tar archive from which the 
    bytes in the file can be read. Yields the file object with the pointer set to the beginning of the
    file. Used for adding files to Docker containers through the Docker Python SDK. Closes and deletes
    the temporary file after the context is closed.

    Args:
        path (``str``): path to the desired file

    Yields:
        ``tempfile.NamedTemporaryFile``: the file with the tar archive written to it
    """
    f = tempfile.NamedTemporaryFile()
    t = tarfile.open(mode="w", fileobj=f)

    path = os.path.abspath(path)
    t.add(path, arcname=os.path.basename(path))

    t.close()
    f.seek(0)

    yield f

    f.close()

@contextmanager
def get_container_file(container, path):
    """
    Retrieves a file at ``path`` from a Docker container ``container``. Reads the bytes of this file
    as a tar archive from the container and writes these bytes to a temporary file. Extracts the single
    member of the tar archive from the temporary file and writes the bytes to another temporary file.
    Yields the file object with the pointer set to the beginning of the file. Closes and deletes the
    temporary files after the context is closed.

    Args:
        container (``docker.models.Container``): the Docker container object
        path (``str``): the path to the file in the container

    Yields:
        ``tempfile.NamedTemporaryFile``: the open temporary file with the extracted contents
    """
    tarf = tempfile.NamedTemporaryFile()
    f = tempfile.NamedTemporaryFile()

    bits, _ = container.get_archive(path)
    for chunk in bits:
        tarf.write(chunk)

    tarf.seek(0)

    tar = tarfile.open(mode="r", fileobj=tarf)

    members = tar.getmembers()
    assert len(members) == 1, "Too many members to extract from container"
    file_contents = tar.extractfile(members[0])
    
    f.write(file_contents.read())
    tar.close()
    tarf.close()
    
    f.seek(0)

    yield f

    f.close()

def list_files(path):
    """
    Returns a list of all non-hidden files in a directory
    
    Args:
        path (``str``): path to a directory
    
    Returns:
        ``list`` of ``str``: list of filenames in the given directory

    """
    return [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)) and file[0] != "."]

def merge_csv(dataframes):
    """
    Merges dataframes along the vertical axis
    
    Args:
        dataframes (``list`` of ``pandas.core.frame.DataFrame``): list of dataframes with same columns
    
    Returns:
        ``pandas.core.frame.DataFrame``: A merged dataframe resulting from 'stacking' all input dataframes

    """
    final_dataframe = pd.concat(dataframes, axis=0, join='inner').sort_index()
    return final_dataframe

def prune_images():
    """
    Prunes all Docker images named ``otter-grade``
    """
    # this is a fix for travis -- allows overriding docker client version
    if os.environ.get("OTTER_DOCKER_CLIENT_VERSION") is not None:
        client = docker.from_env(version=os.environ.get("OTTER_DOCKER_CLIENT_VERSION"))
    else:
        client = docker.from_env()
    
    images = client.images.list()

    for img in images:
        if any([OTTER_DOCKER_IMAGE_TAG in t for t in img.tags]):
            client.images.remove(img.tags[0], force=True)

def generate_hash(path):
    """
    Reads in a file and returns an MD5 hash of its contents.

    Args:
        path (``str``): path to the file that will be read in and hashed

    Returns:
        ``str``: the hash value of the file
    """
    zip_hash = ""
    m = md5()
    with open(path, "rb") as f:
        data = f.read() # read file in chunk and call update on each chunk if file is large.
        m.update(data)
        zip_hash = m.hexdigest()
    return zip_hash
