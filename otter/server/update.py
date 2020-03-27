######################################
##### otter server update Script #####
######################################

import subprocess
import shutil
import os
import yaml
import docker

from subprocess import PIPE
from io import BytesIO
from jinja2 import Template

CLIENT = docker.from_env()

DOCKERFILE_TEMPLATE = Template("""
FROM ucbdsinfra/otter-grader
RUN mkdir /home/notebooks
ADD {{ test_folder_path }} /home{% if test_folder_name != "tests" %}
RUN mv /home/{{ test_folder_name }} /home/tests{% endif %}{% if requirements %}
ADD {{ requirements }} /home
RUN pip3 install /home/{{ requirements_filename }}{% endif %}{% if global_requirements %}
ADD {{ global_requirements }} /home
RUN pip3 install /home/{{ global_requirements_filename }}{% endif %}
""")

def main():
    repo_path = input("What is the absolute path of your assignments repo? [/home/assignments] ")
    if not repo_path:
        repo_path = "/home/assignments"

    assert os.path.exists(repo_path) and os.path.isdir(repo_path), "{} does not exist or is not a directory".format(repo_path)

    os.chdir(repo_path)

    # get commit hash
    commit_hash_cmd = subprocess.run(["git", "rev-parse", "HEAD"], stdout=PIPE, stderr=PIPE)
    assert commit_hash_cmd, commit_hash_cmd.decode("utf-8")

    # get last known commit hash
    with open("/home/.LAST_COMMIT_HASH", "r+") as f:
        last_commit_hash = f.read()

    if last_commit_hash == commit_hash_cmd.stdout:
        
        print("No changes since last pull.")
        return
    
    # parse conf.yml
    assert os.path.isfile("conf.yml"), "conf.yml does not exist"
    with open("conf.yml") as f:
        config = yaml.safe_load(f)

    assignments = config["assignments"]
    ids = [a["assignment_id"] for a in assignments]
    assert len(ids) == len(set(ids)), "Found non-unique assignment IDs in conf.yml"
    # TODO: check for no assignment id conflicts in db

    # TODO: write to the database

    # TODO: start building docker images
    for a in assignments:
        requirements = a["requirements"] if "requirements" in a else ""
        global_requirements = config["requirements"] if "requirements" in config else ""

        dockerfile = DOCKERFILE_TEMPLATE.render(
            test_folder_path = a["tests_path"],
            test_folder_name = os.path.split(a["tests_path"])[1],
            requirements = requirements,
            requirements_filename = os.path.split(requirements)[1],
            global_requirements = global_requirements,
            global_requirements_filename = os.path.split(global_requirements)[1]
        )

        new_image = CLIENT.images.build(
            fileobj=BytesIO(dockerfile.encode("utf-8")), 
            pull=True, 
            tag=a["assignment_id"]
        )

        print("Built Docker image {}".format(new_image.tags))
