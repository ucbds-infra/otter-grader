"""
Otter Service tornado server
"""

import os
import json
import yaml
import hashlib
import jwt
import tornado.options
import queries
import stdio_proxy

from io import BytesIO
from datetime import datetime
from binascii import hexlify
from tornado.httpserver import HTTPServer
from tornado.web import Application, RequestHandler
from tornado.auth import GoogleOAuth2Mixin
from tornado.ioloop import IOLoop
from tornado.queues import Queue
from concurrent.futures import ThreadPoolExecutor

from .utils import connect_db
from ..grade.containers import grade_assignments

OTTER_SERVICE_DIR = "/otter-service"
ARGS = None
SUBMISSION_QUEUE = Queue()
CONN = None
EXECUTOR = ThreadPoolExecutor()

class BaseHandler(tornado.web.RequestHandler):
    """Base login handler"""
    def get_current_user(self):
        """
        Gets secure user cookie for personal authentication
        """
        return self.get_secure_cookie("user")

class LoginHandler(BaseHandler):
    """
    Default auth handler
    
    A login handler that requires instructors to setup users and passwords in database beforehand, 
    allowing students to auth within the notebook.
    """
    async def get(self):
        """
        GET request handler for personal/default authentication login
        """
        username = self.get_argument('username', True)
        password = self.get_argument('password', True)
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        account_check = await self.db.query(
            """
            SELECT * FROM users 
            WHERE username = %s AND password = %s
            """,
            [username, pw_hash]
        )
        if len(account_check) > 0:
            print("Logged in user {} and generating API key".format(username))
            account_check.free()
            api_key = hexlify(os.urandom(32)).decode("utf-8")
            self.write(api_key)
            results = await self.db.query(
                """
                INSERT INTO users (api_keys, username, password) VALUES (%s, %s, %s)
                ON CONFLICT (username)
                DO UPDATE SET api_keys = array_append(users.api_keys, %s)
                """,
                [[api_key], username, pw_hash, api_key]
            )
            results.free()
        else:
            print("Failed login attempt for user {}".format(username))
            account_check.free()
            self.clear()
            self.set_status(401)
            self.finish()

    @property
    def db(self):
        return self.application.db

class GoogleOAuth2LoginHandler(RequestHandler, GoogleOAuth2Mixin):
    async def get(self):
        """
        GET request handler for Google OAuth

        Handler for authenticating users with Google OAuth. Requires that user sets environment
        variables containing their client key and secret. Provides users with an API key that they
        can enter in the notebook by way of authenticating.
        """
        if not self.get_argument('code', False):
            print("Redirecting user to Google OAuth")
            return self.authorize_redirect(
                redirect_uri=self.settings['auth_redirect_uri'],
                client_id = ARGS.google_key if ARGS.google_key else self.settings['google_oauth']['key'],
                client_secret = ARGS.google_secret if ARGS.google_secret else self.settings['google_oauth']['secret'],
                scope=['email', 'profile'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'}
            )
        else:
            resp = await self.get_authenticated_user(
                redirect_uri=self.settings['auth_redirect_uri'],
                code=self.get_argument('code')
            )
            api_key = hexlify(os.urandom(32)).decode("utf-8")
            email = jwt.decode(resp['id_token'], verify=False)['email']
            print("Generating API key for user {} from Google OAuth".format(email))
            results = await self.db.query(
                """
                INSERT INTO users (api_keys, email) VALUES (%s, %s)
                ON CONFLICT (email) 
                DO UPDATE SET api_keys = array_append(users.api_keys, %s)
                """,
                [[api_key], email, api_key]
            )
            results.free()

            self.render("templates/api_key.html", key=api_key)

    @property
    def db(self):
        return self.application.db

class SubmissionHandler(RequestHandler):
    """
    Processes and validates student submission

    Handler for processing and validating a student's submission. Ensure that notebook is present
    and valid, checks API key, and implements rate limiting to prevent spamming the autograder.
    Queues submission for grading by ``EXECUTOR``.
    """
    async def get(self):
        """
        GET request handler. Route warns users that this is a POST-only route.
        """
        self.write("This is a POST-only route; you probably shouldn't be here.")
        self.finish()

    async def post(self):
        """
        POST request handler. Validates JSON params and queues submission for grading.
        """
        self.submission_id = None
        try:
            # check request params
            request = tornado.escape.json_decode(self.request.body)
            assert 'nb' in request.keys(), 'submission contains no notebook'
            assert 'api_key' in request.keys(), 'missing api key'

            notebook = request['nb']
            api_key = request['api_key']
            
            # run through submission
            await self.submit(notebook, api_key)
        except Exception as e:
            print(e)
        self.finish()

        # if submission successful, queue notebook for grading
        if self.submission_id is not None:
            SUBMISSION_QUEUE.put(self.submission_id)

    async def validate(self, notebook, api_key):
        """
        Ensures a submision is valid by checking user credentials, submission frequency, and
        validity of notebook file.

        Arguments:
            notebook (``dict``): notebook in JSON form
            api_key (``str``): API key generated during submission

        Returns:
            ``tuple``: submission information
        """
        # authenticate user with api_key
        results = await self.db.query("SELECT user_id, username, email FROM users WHERE %s=ANY(api_keys) LIMIT 1", [api_key])
        user_id = results.as_dict()['user_id'] if len(results) > 0 else None
        username = results.as_dict()['username'] or results.as_dict()['email'] if len(results) > 0 else None
        results.free()
        assert user_id, 'invalid API key: {}'.format(api_key)

        # get assignment and class id from notebook metadata
        assert all(key in notebook for key in ['metadata', 'nbformat', 'cells']), 'invalid Jupyter notebook'
        assert 'assignment_id' in notebook['metadata'], 'missing required metadata attribute: assignment_id'
        assert 'class_id' in notebook['metadata'], 'missing required metadata attribute: class_id'
        assignment_id = notebook['metadata']['assignment_id']
        class_id = notebook['metadata']['class_id']

        # rate limiting
        results = await self.db.query(
            """
            SELECT timestamp 
            FROM submissions 
            WHERE user_id = %s AND assignment_id = %s AND class_id = %s
            ORDER BY timestamp DESC 
            LIMIT 1
            """, 
            (user_id, assignment_id, class_id)
        )
        last_submitted = results.as_dict()['timestamp'] if len(results) > 0 else None
        results.free()

        if last_submitted:
            delta = datetime.utcnow() - last_submitted
            # rate_limit = 120
            if delta.seconds < ARGS.rate_limit:
                self.write_error(429, message='Please wait {} second(s) before re-submitting.'.format(ARGS.rate_limit - delta.seconds))
                return
        
        # check that assignment exists
        results = await self.db.query("SELECT * FROM assignments WHERE assignment_id=%s LIMIT 1", [assignment_id])
        assert results, 'assignment_id {} not found on server'.format(assignment_id)
        assignment = results.as_dict()
        results.free()

        return (user_id, username, assignment['class_id'], assignment_id, assignment['assignment_name'])

    async def submit(self, notebook, api_key):
        """
        If valid submission, inserts notebook into submissions table in database and queues it 
        for grading.

        Arguments:
            notebook (``dict``): notebook in JSON form
            api_key (``str``): API key generated during submission
        """
        try:
            user_id, username, class_id, assignment_id, assignment_name = await self.validate(notebook, api_key)
        except TypeError as e:
            print("Submission failed for user with API key {}: ".format(api_key, e))
            return
        except AssertionError as e:
            print("Submission failed for user with API key {} due to due to client error: {}".format(api_key, e))
            self.write_error(400, message=e)
            return

        # fetch next submission id
        results = await self.db.query("SELECT nextval(pg_get_serial_sequence('submissions', 'submission_id')) as id")
        submission_id = results.as_dict()['id']
        results.free()

        print("Successfully received submission {} from user {}".format(submission_id, username))

        # save notebook to disk
        dir_path = os.path.join(
            self.settings['notebook_dir'],
            'class-{}'.format(class_id),
            'assignment-{}'.format(assignment_id),
            'submission-{}'.format(submission_id)
        )
        file_path = os.path.join(dir_path, '{}.ipynb'.format(assignment_name))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(file_path, 'w') as f:
            json.dump(notebook, f)

        print("Successfully saved submission {} at {}".format(submission_id, file_path))
        
        # store submission to database
        results = await self.db.query("INSERT INTO submissions (submission_id, assignment_id, class_id, user_id, file_path, timestamp) VALUES (%s, %s, %s, %s, %s, %s)",
                                            [submission_id, assignment_id, class_id, user_id, file_path, datetime.utcnow()])
        assert results, 'submission failed'
        results.free()

        self.submission_id = submission_id

        self.write('Submission {} received.'.format(submission_id))

    @property
    def db(self):
        return self.application.db

    def write_error(self, status_code, **kwargs):
        """
        Writes an error message to response

        Args:
            status_code (``int``): the response status
            message (``str``): message to include in the response
        """
        if 'message' in kwargs:
            self.write('Submission failed: {}'.format(kwargs['message']))
        else:
            self.write('Submission failed.')

def grade_submission(submission_id):
    """
    Grades a single submission with id ``submission_id``

    Args:
        submission_id (``str``): the id of the submission to grade

    Returns:
        ``tuple``: grading message and results dataframe for printing
    """
    global CONN
    cursor = CONN.cursor()

    cursor.execute(
        """
        SELECT user_id, submission_id, assignment_id, class_id, file_path 
        FROM submissions 
        WHERE submission_id = %s 
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (submission_id, )
    )
    user_record = cursor.fetchall()
    assert len(user_record) == 1, "Submission {} not found".format(submission_id)
    row = user_record[0]
    user_id = int(row[0])
    submission_id = int(row[1])
    assignment_id = str(row[2])
    class_id = str(row[3])
    file_path = str(row[4])

    cursor.execute(
        """
        SELECT seed
        FROM assignments
        WHERE assignment_id = %s AND class_id = %s
        """,
        (assignment_id, class_id)
    )
    assignment_record = cursor.fetchall()
    assert len(assignment_record) == 1, "Assignment {} for class {} not found".format(assignment_id, class_id)
    seed = int(assignment_record[0][0]) if assignment_record[0][0] else None

    cursor.execute(
        """
        SELECT username, email 
        FROM users 
        WHERE user_id = %s
        LIMIT 1
        """,
        (user_id, )
    )
    user_record = cursor.fetchall()
    row = user_record[0]
    username = str(row[0] or row[1])

    # Run grading function in a docker container
    stdout = BytesIO()
    stderr = BytesIO()
    try:
        with stdio_proxy.redirect_stdout(stdout), stdio_proxy.redirect_stderr(stderr):
            df = grade_assignments(
                tests_dir=None, 
                notebooks_dir=file_path, 
                id=assignment_id, 
                image=class_id + "-" + assignment_id,
                debug=True,
                verbose=True,
                seed=seed
            )
            
        message = "Graded submission {} from user {}".format(submission_id, username)

        df_json_str = df.to_json()
    
        # Insert score into submissions table
        cursor.execute(
            """
            UPDATE submissions
            SET score = %s
            WHERE submission_id = %s
            """,
            (df_json_str, submission_id)
        )

    finally:
        stdout = stdout.getvalue().decode("utf-8")
        stderr = stderr.getvalue().decode("utf-8")
        with open(os.path.join(os.path.split(file_path)[0], "GRADING_STDOUT"), "w+") as f:
            f.write(stdout)
        with open(os.path.join(os.path.split(file_path)[0], "GRADING_STDERR"), "w+") as f:
            f.write(stderr)
    
    cursor.close()
    return message, df

async def start_grading_queue(shutdown=False):
    """
    Pops submission ids off ``SUBMISSION_QUEUE`` and sending them into ``EXECUTOR`` to be graded
    
    Args:
        shutdown (``bool``): whether or not to shutdown EXECUTOR after processing queue; default 
            ``False``
    """
    global SUBMISSION_QUEUE

    async for submission_id in SUBMISSION_QUEUE:
        future = EXECUTOR.submit(
            grade_submission,
            submission_id
        )
        future.add_done_callback(lambda f: print(f.result()[0], "\n", f.result()[1]))

        # Set task done in queue
        SUBMISSION_QUEUE.task_done()
    
    if shutdown:
        EXECUTOR.shutdown(wait=True)

class Application(tornado.web.Application):
    """
    Otter Service tornado application
    """
    def __init__(self):
        """
        Initialize tornado server for receiving/grading submissions
        """
        endpoint = ARGS.endpoint or os.environ.get("OTTER_ENDPOINT", None)
        assert endpoint is not None, "no endpoint address provided"
        assert os.path.isdir(OTTER_SERVICE_DIR), "{} does not exist".format(OTTER_SERVICE_DIR)
        settings = dict(
            google_oauth={
                "key": ARGS.google_key or os.environ.get("GOOGLE_CLIENT_KEY", None), 
                "secret": ARGS.google_secret or os.environ.get("GOOGLE_CLIENT_SECRET", None)
            },
            notebook_dir = os.path.join(OTTER_SERVICE_DIR, "submissions"),
            auth_redirect_uri = os.path.join(endpoint, "auth/callback")
        )
        handlers = [
            (r"/submit", SubmissionHandler),
            (r"/auth/google", GoogleOAuth2LoginHandler),
            (r"/auth/callback", GoogleOAuth2LoginHandler),
            (r"/auth", LoginHandler)
        ]
        tornado.web.Application.__init__(self, handlers, **settings)
        
        # Initialize database session
        self.db = queries.TornadoSession(queries.uri(
            host=ARGS.db_host,
            port=ARGS.db_port,
            dbname='otter_db',
            user=ARGS.db_user,
            password=ARGS.db_pass
        ))

def main(cli_args):
    """
    Starts Otter Service tornado server

    Args:
        cli_args (``argparse.Namespace``): parsed command-line arguments
    """
    # if args.missing_packages:
    #     raise ImportError(
    #         "Missing some packages required for otter service. "
    #         "Please install all requirements at "
    #         "https://raw.githubusercontent.com/ucbds-infra/otter-grader/master/requirements.txt"
    #     )

    global CONN
    global ARGS

    ARGS = cli_args
    CONN = connect_db(ARGS.db_host, ARGS.db_user, ARGS.db_pass, ARGS.db_port)

    port = ARGS.port
    tornado.options.parse_command_line()

    # make submissions forlder
    if not os.path.isdir(OTTER_SERVICE_DIR):
        os.makedirs(os.path.join(OTTER_SERVICE_DIR))
    
    server = HTTPServer(Application())
    server.listen(port)
    print("Listening on port {}".format(port))

    IOLoop.current().add_callback(start_grading_queue)
    IOLoop.current().start()
