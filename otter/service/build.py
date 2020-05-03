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
from psycopg2.errors import UniqueViolation

from ..utils import connect_db

DOCKERFILE_TEMPLATE = Template("""
FROM ucbdsinfra/otter-grader
RUN mkdir /home/notebooks
ADD {{ test_folder_path }} /home{% if test_folder_name != "tests" %}
RUN mv /home/{{ test_folder_name }} /home/tests{% endif %}{% if requirements %}
ADD {{ requirements }} /home
RUN pip3 install -r /home/{{ requirements_filename }}{% endif %}{% if global_requirements %}
ADD {{ global_requirements }} /home
RUN pip3 install -r /home/{{ global_requirements_filename }}{% endif %}
""")

def write_class_info(class_name, conn):
    """Writes the given class_name to the database, auto-generating a class_id

    Args:
        class_name (str): Name of new class to add to the database
        conn (Connection): Connection object for database
    
    Returns:
        class_id: Class ID for newly added class.
    """
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
    """Inserts/Updates assignment class_id and assignment_name in database. Inserts if assignment_id
        is not present. Updates if assignment_id is present.

    Args:
        assignment_id (str): Assignment id which will be created or updated
        class_id (str): Class id to insert/update
        assignment_name (str): Assignment name to insert/update
        conn (Connection): Connection object for database
    """
    cursor = conn.cursor()
    find_sql_command = """SELECT * FROM assignments
    WHERE assignment_id = '{}' AND class_id = '{}'
    """.format(assignment_id, class_id)
    cursor.execute(find_sql_command)

    # If conflict on assignment_id, class_id
    # Update assignment_name
    if cursor.rowcount == 1:
        sql_command = """UPDATE assignments
                        SET assignment_name = '{}'
                        WHERE assignment_id = '{}' AND class_id = '{}'
                        """.format(assignment_id, class_id, assignment_name, assignment_name)
        cursor.execute(find_sql_command)
    # Else, just insert
    else:
        sql_command = """INSERT INTO assignments (assignment_id, class_id, assignment_name)
                        VALUES('{}', {}, '{}')
                        """.format(assignment_id, class_id, assignment_name, assignment_name)
        cursor.execute(find_sql_command)

    cursor.execute(sql_command)
    conn.commit()
    cursor.close()

def main(args, conn=None, close_conn=True):
    # repo_path = input("What is the absolute path of your assignments repo? [/home/assignments] ")
    # if not repo_path:
    #     repo_path = "/home/assignments"

    repo_path = args.repo_path
    assert os.path.exists(repo_path) and os.path.isdir(repo_path), "{} does not exist or is not a directory".format(repo_path)

    current_dir = os.getcwd()
    os.chdir(repo_path)

    # parse conf.yml
    assert os.path.isfile("conf.yml"), "conf.yml does not exist"
    with open("conf.yml") as f:
        config = yaml.safe_load(f)

    assignments = config["assignments"]
    name_id_pairs = [(a["name"], a["assignment_id"]) for a in assignments]
    ids = [a["assignment_id"] for a in assignments]
    assert len(ids) == len(set(ids)), "Found non-unique assignment IDs in conf.yml"

    # Use one global connection for all db-related commands
    # TODO: fill in the arguments
    if conn is None:
        conn = connect_db("", "", "")
    class_id = write_class_info(config["course"], conn)

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

        # Build the docker image
        echo_dockerfile = subprocess.Popen(["echo", dockerfile], stdout=PIPE)
        echo_dockerfile.wait()
        build_out = subprocess.run(
            ["docker", "build", "-f", "-", ".", "-t", a["assignment_id"]],
            stdin=echo_dockerfile.stdout, stdout=PIPE
        )
        echo_dockerfile.stdout.close()

        print("Built Docker image {}".format(a["assignment_id"]))
    
    if close_conn:
        conn.close()
    
    os.chdir(current_dir)
