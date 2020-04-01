######################################
##### otter server create Script #####
######################################

MISSING_PACKAGES = False

try:
    from psycopg2 import connect, extensions, sql
    import yaml
    import csv
except ImportError:
    # don't need requirements to use otter without otter service
    MISSING_PACKAGES = True

with open("conf.yml") as f:
    config = yaml.safe_load(f)

def connect_db(host=config["db_host"], username=config["db_user"], password=config["db_pass"]):
    conn = connect(dbname='otter_db',
               user=username,
               host=host,
               password=password)
    conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn

def create_users(filepath):
    with open(filepath, newline='') as csvfile:
        filereader = csv.reader(csvfile, delimiter=',', quotechar='|')
        conn = connect_db()
        cursor = conn.cursor()
        for row in filereader:
            username, password = row[:2]
            if username.lower() == "username":
                # skip heading
                continue
            insert_command = """
                INSERT INTO users (username, password) VALUES (\'{}\', \'{}\')
                ON CONFLICT (username)
                DO UPDATE SET password = \'{}\'
                """.format(username, password, password)
            cursor.execute(insert_command)

def main(args):
    if MISSING_PACKAGES:
        raise ImportError(
            "Missing some packages required for otter service. "
            "Please install all requirements at "
            "https://raw.githubusercontent.com/ucbds-infra/otter-grader/master/requirements.txt"
        )

    with open("conf.yml") as f:
        config = yaml.safe_load(f)
    
    conn = connect(dbname='postgres',
                   host=config['db_host'],
                   port=config['db_port'],
                   user=config['db_user'],
                   password=config['db_pass'])

    conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE otter_db')
    cursor.close()
    conn.close()

    conn = connect(dbname='otter_db',
                   host=config['db_host'],
                   port=config['db_port'],
                   user=config['db_user'],
                   password=config['db_pass'])

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
            class_id SERIAL PRIMARY KEY,
            class_name TEXT NOT NULL
        )
        ''',
        '''
        CREATE TABLE assignments (
            assignment_id TEXT PRIMARY KEY,
            class_id INTEGER REFERENCES classes (class_id) NOT NULL,
            assignment_name TEXT NOT NULL
        )
        ''',
        '''
        CREATE TABLE submissions (
            submission_id SERIAL PRIMARY KEY,
            assignment_id TEXT REFERENCES assignments(assignment_id) NOT NULL,
            user_id INTEGER REFERENCES users(user_id) NOT NULL,
            file_path TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            score JSONB
        )
        '''
    ]

    for query in queries:
        cursor.execute(query)
        
    cursor.close()
    conn.close()
