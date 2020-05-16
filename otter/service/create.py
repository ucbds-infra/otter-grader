#############################################
##### Create Database for Otter Service #####
#############################################

MISSING_PACKAGES = False

try:
    import yaml
    import csv
    import psycopg2
    import hashlib
    import os

    from psycopg2 import connect, extensions, sql
    from psycopg2.errors import DuplicateTable

    from ..utils import connect_db

except ImportError:
    # don't need requirements to use otter without otter service
    MISSING_PACKAGES = True

def create_users(filepath, host=None, username=None, password=None, conn=None):
    """
    Inserts usernames from filepath into db

    Args:
        filepath (str): Path to CSV files with usernames in first column, 
            passwords in second
        host (str, optional): Hostname where postgresql is running
        username (str, optional): Username for writing to postgres database
        password (str, optional): Password corresponding to provided username
    """
    with open(filepath, newline='') as csvfile:
        filereader = csv.reader(csvfile, delimiter=',', quotechar='|')
        # TODO: fill in the arguments below
        if conn is None:
            conn = connect_db(host, username, password)
        cursor = conn.cursor()
        for row in filereader:
            username, password = row[:2]
            password = hashlib.sha256(password.encode()).hexdigest()
            if username.lower() == "username":
                # skip heading
                continue
            insert_command = """
                INSERT INTO users (username, password) VALUES (\'{}\', \'{}\')
                ON CONFLICT (username)
                DO UPDATE SET password = \'{}\'
                """.format(username, password, password)
            cursor.execute(insert_command)

def remove_users(filepath, host=None, username=None, password=None, conn=None):
    """Removes users specified in file FILEPATH
    
    Args:
        filepath (str): Path to CSV files with usernames in first column, 
            passwords in second
        host (str, optional): Hostname where postgresql is running
        username (str, optional): Username for writing to postgres database
        password (str, optional): Password corresponding to provided username
    """
    with open(filepath, newline='') as csvfile:
        filereader = csv.reader(csvfile, delimiter=',', quotechar='|')
        # TODO: fill in the arguments below
        if conn is None:
            conn = connect_db(host, username, password)
        cursor = conn.cursor()
        remove_count = 0
        for row in filereader:
            username, password = row[:2]
            password = hashlib.sha256(password.encode()).hexdigest()
            if username.lower() == "username":
                # skip heading
                continue
            insert_command = """
                DELETE FROM users WHERE username = \'{}\'
                """.format(username)
            cursor.execute(insert_command)

def main(args, conn=None, close_conn=True):
    """
    conn is arg to pre-made db connection
    """
    if MISSING_PACKAGES:
        raise ImportError(
            "Missing some packages required for otter service. "
            "Please install all requirements at "
            "https://raw.githubusercontent.com/ucbds-infra/otter-grader/master/requirements.txt"
        )

    # # # TODO: can't assume we're in directory with conf.yml
    # # with open("conf.yml") as f:
    # #     config = yaml.safe_load(f)
    # try:
    #     assert os.path.isfile("conf.yml"), "conf.yml does not exist"
    #     with open("conf.yml") as f:
    #         config = yaml.safe_load(f)
    # except AssertionError:
    #     conf_path = input("What is the path of your config file?")
    #     with open(conf_path) as f:
    #         config = yaml.safe_load(f)
    pgconn = connect_db(args.db_host, args.db_user, args.db_pass, args.db_port, db='postgres')

    try:
        pgconn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = pgconn.cursor()
        cursor.execute('CREATE DATABASE otter_db')
    except psycopg2.errors.DuplicateDatabase:
        pass
    finally: 
        cursor.close()
        pgconn.close()

    if conn is None:
        conn = connect_db(args.db_host, args.db_user, args.db_pass, args.db_port)

    # conn = connect_db(args.db_host, args.db_user, args.db_pass, args.db_port)

    conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    queries = [
        '''
        CREATE TABLE users (
            user_id SERIAL PRIMARY KEY,
            api_keys VARCHAR[] CHECK (cardinality(api_keys) > 0),
            username TEXT UNIQUE,
            password VARCHAR,
            email TEXT UNIQUE,
            CONSTRAINT has_username_or_email CHECK (username IS NOT NULL or email IS NOT NULL)
        )
        ''',
        '''
        CREATE TABLE classes (
            class_id TEXT PRIMARY KEY,
            class_name TEXT NOT NULL
        )
        ''',
        '''
        CREATE TABLE assignments (
            assignment_id TEXT NOT NULL,
            class_id TEXT REFERENCES classes (class_id) NOT NULL,
            assignment_name TEXT NOT NULL,
            seed INTEGER,
            PRIMARY KEY (assignment_id, class_id)
        )
        ''',
        '''
        CREATE TABLE submissions (
            submission_id SERIAL PRIMARY KEY,
            assignment_id TEXT NOT NULL,
            class_id TEXT NOT NULL,
            user_id INTEGER REFERENCES users(user_id) NOT NULL,
            file_path TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            score JSONB,
            FOREIGN KEY (assignment_id, class_id) REFERENCES assignments (assignment_id, class_id)
        )
        '''
    ]

    for query in queries:
        try:
            cursor.execute(query)
        except DuplicateTable:
            pass
        
    cursor.close()
    if close_conn:
        conn.close()
