MISSING_PACKAGES = False

try:
    from psycopg2 import connect, extensions
except ImportError:
    MISSING_PACKAGES = True

def connect_db(host="localhost", username="admin", password="", port="5432", db="otter_db"):
    """Connects to a specific Postgres database with provided parameters/credentials

    Arguments:
        host (``str``, optional): hostname for database (default 'localhost')
        username (``str``, optional): username with proper read/write permissions for Postgres
        password (``str``, optional): password for provided username
        port (``str``, optional): port on which Postgres is running

    Returns:
        ``connection``: connection object for executing SQL commands on Postgres database

    Raises:
        ``ImportError``: if psycopg2 is not installed
    """
    if MISSING_PACKAGES:
        raise ImportError(
            "Missing some packages required for otter service. "
            "Please install all requirements at "
            "https://raw.githubusercontent.com/ucbds-infra/otter-grader/master/requirements.txt"
        )
        
    conn = connect(dbname=db,
               user=username,
               host=host,
               password=password,
               port=port)
    conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn
