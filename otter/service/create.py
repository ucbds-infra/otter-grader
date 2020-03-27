######################################
##### otter server create Script #####
######################################

from psycopg2 import connect, extensions, sql

def main():
    conn = connect(dbname='postgres',
                user='admin',
                host='',
                password='')

    conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE otter_db')
    cursor.close()
    conn.close()

    conn = connect(dbname='otter_db',
                user='admin',
                host='',
                password='')

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
            assignment_id SERIAL PRIMARY KEY,
            class_id INTEGER REFERENCES classes (class_id) NOT NULL,
            assignment_name TEXT NOT NULL
        )
        ''',
        '''
        CREATE TABLE submissions (
            submission_id SERIAL PRIMARY KEY,
            assignment_id INTEGER REFERENCES assignments(assignment_id) NOT NULL,
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
