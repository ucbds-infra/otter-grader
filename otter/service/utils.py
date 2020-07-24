"""
Utilities for Otter Service
"""

from psycopg2 import connect, extensions

def connect_db(host="localhost", username="admin", password="", port="5432", db="otter_db"):
    """Connects to a specific Postgres database with provided parameters/credentials

    Arguments:
        host (``str``, optional): hostname for database (default 'localhost')
        username (``str``, optional): username with proper read/write permissions for Postgres
        password (``str``, optional): password for provided username
        port (``str``, optional): port on which Postgres is running

    Returns:
        ``psycopg2.connection``: connection object for executing SQL commands on Postgres database

    Raises:
        ``ImportError``: if psycopg2 is not installed
    """
    
    conn = connect(dbname=db,
               user=username,
               host=host,
               password=password,
               port=port)
    conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn
