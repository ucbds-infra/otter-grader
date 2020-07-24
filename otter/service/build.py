"""
Docker image building for Otter Service
"""

import subprocess
import shutil
import os
import yaml

from subprocess import PIPE, DEVNULL
from io import BytesIO
from jinja2 import Template
from psycopg2.errors import UniqueViolation

from .utils import connect_db

DOCKERFILE_TEMPLATE = Template("""
FROM {{ image }}
RUN mkdir /home/notebooks
ADD {{ test_folder_path }} /home/tests{% if global_requirements %}
ADD {{ global_requirements }} /home
RUN pip3 install -r /home/{{ global_requirements_filename }}{% endif %}{% if requirements %}
ADD {{ requirements }} /home
RUN pip3 install -r /home/{{ requirements_filename }}{% endif %}{% for file in files %}
ADD {{ file }} /home/notebooks{% endfor %}
""")

def write_class_info(class_id, class_name, conn):
    """
    Writes the given ``class_name`` to the database

    Args:
        class_id (``str``): the class id for the database
        class_name (``str``): name of new class to add to the database
        conn (``psycopg2.connection``): connection object for database
    
    Returns:
        ``str``: class id for newly added class
    """
    cursor = conn.cursor()
    insert_command = "INSERT INTO classes (class_id, class_name) \
        VALUES(%s, %s)"#.format(class_name)
    try:
        cursor.execute(insert_command, (class_id, class_name))
    except UniqueViolation:
        pass
    conn.commit()
    cursor.close()
    return class_id

def write_assignment_info(assignment_id, class_id, assignment_name, seed, conn):
    """
    Inserts or updates an assignment with p-key ``(class_id, assignment_id)`` in the ``assignments`` 
    table of the database.

    Args:
        assignment_id (``str``): assignment id which will be created or updated
        class_id (``str``): class id of the assignment
        assignment_name (``str``): assignment name to insert/update
        conn (``psycopg2.connection``): connection object for database
    """
    cursor = conn.cursor()
    find_sql_command = """SELECT * FROM assignments
    WHERE assignment_id = '{}' AND class_id = '{}'
    """.format(assignment_id, class_id)
    cursor.execute(find_sql_command)

    # if seed is None:
    #     seed = "NULL"

    # If conflict on assignment_id, class_id
    # Update assignment_name
    if cursor.rowcount == 1:
        sql_command = """UPDATE assignments
                        SET assignment_name = %s, seed = %s
                        WHERE assignment_id = %s AND class_id = %s
                        """#.format(assignment_id, class_id, assignment_name, assignment_name)
        cursor.execute(sql_command, (assignment_name, seed, assignment_id, class_id))
    # Else, just insert
    else:
        sql_command = """INSERT INTO assignments (assignment_id, class_id, assignment_name, seed)
                        VALUES (%s, %s, %s, %s)
                        """#.format(assignment_id, class_id, assignment_name, assignment_name)
        cursor.execute(sql_command, (assignment_id, class_id, assignment_name, seed))

    conn.commit()
    cursor.close()

def main(args, conn=None, close_conn=True):
    """
    Inserts/updates assignment records in the database and builds Docker images from configuration
    repository based on a YAML configuation file.

    Args:
        args (``argparse.Namespace``): parsed command-line arguments
        conn (``psycopg2.connection``, optional): Postgres connection
        close_conn (``bool``, optional): whether to close the databse connection after running; 
            default ``True``
    """
    # if args.missing_packages:
    #     raise ImportError(
    #         "Missing some packages required for otter service. "
    #         "Please install all requirements at "
    #         "https://raw.githubusercontent.com/ucbds-infra/otter-grader/master/requirements.txt"
    #     )

    repo_path = args.repo_path
    assert os.path.exists(repo_path) and os.path.isdir(repo_path), "{} does not exist or is not a directory".format(repo_path)

    current_dir = os.getcwd()
    os.chdir(repo_path)

    # parse conf.yml
    assert os.path.isfile("conf.yml"), "conf.yml does not exist"
    with open("conf.yml") as f:
        config = yaml.safe_load(f)

    assignments = config["assignments"]
    assignment_cfs = [(a["name"], a["assignment_id"], a.get("seed", None)) for a in assignments]
    ids = [a["assignment_id"] for a in assignments]
    assert len(ids) == len(set(ids)), "Found non-unique assignment IDs in conf.yml"

    # Use one global connection for all db-related commands
    if conn is None:
        conn = connect_db(args.db_host, args.db_user, args.db_pass, args.db_port)
    class_id = write_class_info(config["class_id"], config["class_name"], conn)

    # write to the database
    for name, assignment_id, seed in assignment_cfs:
        write_assignment_info(assignment_id, class_id, name, seed, conn)

    # TODO: start building docker images
    for a in assignments:
        requirements = a["requirements"] if "requirements" in a else ""
        global_requirements = config["requirements"] if "requirements" in config else ""

        dockerfile = DOCKERFILE_TEMPLATE.render(
            image = args.image,
            test_folder_path = a["tests_path"],
            test_folder_name = os.path.split(a["tests_path"])[1],
            requirements = requirements,
            requirements_filename = os.path.split(requirements)[1],
            global_requirements = global_requirements,
            global_requirements_filename = os.path.split(global_requirements)[1],
            files = a.get("files", [])
        )

        print("Building Docker image {}".format(class_id + "-" + a["assignment_id"]))
        
        # Build the docker image
        echo_dockerfile = subprocess.Popen(["echo", dockerfile], stdout=PIPE)
        echo_dockerfile.wait()
        
        build_out = subprocess.Popen(
            ["docker", "build", "-f", "-", ".", "-t", class_id + "-" + a["assignment_id"]],
            stdin=echo_dockerfile.stdout, 
            stdout=DEVNULL if args.quiet else None
        )
        build_out.wait()
        
        echo_dockerfile.stdout.close()

        print("Built Docker image {}".format(class_id + "-" + a["assignment_id"]))
    
    if close_conn:
        conn.close()
    
    os.chdir(current_dir)
