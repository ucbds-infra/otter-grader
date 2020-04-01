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
from psycopg2 import connect, extensions, sql

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

with open("conf.yml") as f:
    config = yaml.safe_load(f)

def connect_db(host=config["db_host"], username=config["db_user"], password=config["db_pass"]):
    conn = connect(dbname='otter_db',
               user=username,
               host=host,
               password=password)
    conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn

def check_assignment_id(assignment_ids, conn):
    cursor = conn.cursor()
    total_row_matches = 0
    duplicate_ids = []
    for i, assignment_id in enumerate(assignment_ids):
        sql_command = "SELECT * FROM assignments WHERE assignment_id = {}".format(i)
        cursor.execute(sql_command)
        if cursor.rowcount > 0:
            duplicate_ids.append(assignment_id)
        total_row_matches += cursor.rowcount
    cursor.close()
    return total_row_matches == 0, duplicate_ids

def write_class_info(class_name, conn):
    cursor = conn.cursor()
    insert_command = "INSERT INTO classes (class_name) \
        VALUES(\'{}\')".format(class_name)
    cursor.execute(insert_command)
    select_command = "SELECT class_id FROM classes \
        WHERE class_name = \'{}\'".format(class_name)
    cursor.execute(select_command)
    select_result = cursor.fetchall()
    class_id = None
    for row in select_result:
        class_id = row[0]
    conn.commit()
    cursor.close()
    return class_id

def write_assignment_info(assignment_id, class_id, assignment_name, conn):
    cursor = conn.cursor()
    sql_command = """INSERT INTO assignments (assignment_id, class_id, assignment_name)
                    VALUES(\'{}\', {}, \'{}\')
                    ON CONFLICT (assignment_id, class_id)
                    DO UPDATE SET assignment_name = \'{}\'
                    """.format(assignment_id, class_id, assignment_name, assignment_name)
    cursor.execute(sql_command)
    conn.commit()
    cursor.close()

def main(args):
    repo_path = input("What is the absolute path of your assignments repo? [/home/assignments] ")
    if not repo_path:
        repo_path = "/home/assignments"

    assert os.path.exists(repo_path) and os.path.isdir(repo_path), "{} does not exist or is not a directory".format(repo_path)

    os.chdir(repo_path)

    # # get commit hash
    # commit_hash_cmd = subprocess.run(["git", "rev-parse", "HEAD"], stdout=PIPE, stderr=PIPE)
    # assert not commit_hash_cmd.stderr, commit_hash_cmd.stderr.decode("utf-8")

    # # get last known commit hash
    # TODO: Create file if not exists
    # with open("/home/.LAST_COMMIT_HASH", "r+") as f:
    #     last_commit_hash = f.read()

    # if last_commit_hash == commit_hash_cmd.stdout:
    #     # write commit hash
    #     with open("/home/.LAST_COMMIT_HASH", "w+") as f:
    #         f.write(commit_hash_cmd.stdout)
        
    #     print("No changes since last pull.")
    #     return
    
    # parse conf.yml
    assert os.path.isfile("conf.yml"), "conf.yml does not exist"
    with open("conf.yml") as f:
        config = yaml.safe_load(f)
    assignments = config["assignments"]
    name_id_pairs = [(a["name"], a["assignment_id"]) for a in assignments]
    ids = [a["assignment_id"] for a in assignments]
    assert len(ids) == len(set(ids)), "Found non-unique assignment IDs in conf.yml"
    
    # Use one global connection for all db-related commands
    conn = connect_db() 
    class_id = write_class_info(config["course"], conn)
    
    # check for no assignment id conflicts in db
    found_match, duplicate_ids = check_assignment_id(ids, conn)
    assert found_match, "Ids: {} are already in the database".format(duplicate_ids)
    
    # write to the database
    for name, assignment_id in name_id_pairs:
        write_assignment_info(assignment_id, class_id, name, conn)
    
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

        # with open("DOCKERFILE", "w+") as f:
        #     f.write(str(dockerfile))

        # Build the docker image
        echo_dockerfile = subprocess.run(["echo", dockerfile], stdout=PIPE, stderr=PIPE)
        assert not echo_dockerfile.stderr, echo_dockerfile.stderr.decode("utf-8")
        build_out = subprocess.run(
            ["docker", "build", "-", "-t", a["assignment_id"]], 
            stdin=echo_dockerfile.stdout, stdout=PIPE, stderr=PIPE
        )
        assert not build_out.stderr, build_out.stderr.decode("utf-8")

        # new_image = CLIENT.images.build(
        #     fileobj=BytesIO(dockerfile.encode("utf-8")), 
        #     pull=True,
        #     tag=a["assignment_id"]
        # )
        # print("Built Docker image {}".format(new_image.tags))

        print("Built Docker image {}".format(a["assignment_id"]))
