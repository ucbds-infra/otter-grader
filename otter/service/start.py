#####################################
##### otter server start Script #####
#####################################

MISSING_PACKAGES = False

try:
    import os
    import json
    import yaml
    import hashlib
    import jwt
    import logging
    import contextlib
    import traceback
    import tornado.options
    import queries

    from io import StringIO
    from datetime import datetime
    from binascii import hexlify
    from tornado.httpserver import HTTPServer
    from tornado.web import Application, RequestHandler
    from tornado.auth import GoogleOAuth2Mixin
    from tornado.ioloop import IOLoop
    from tornado.queues import Queue
    from tornado.gen import sleep
    # from psycopg2 import connect, extensions

    from ..containers import grade_assignments
    from ..utils import connect_db

    OTTER_SERVICE_DIR = "/otter-service"

    args = None

    user_queue = Queue()

    conn = None

    # assert args.config is not None, "no config provided"
    # with open(args.config) as f:
    #     config = yaml.load(f)

    class BaseHandler(tornado.web.RequestHandler):
        def get_current_user(self):
            """Gets secure user cookie for personal authentication
            """
            return self.get_secure_cookie("user")

    class LoginHandler(BaseHandler):
        async def get(self):
            """
            Get request for personal/default authentication login
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
            Get request for Google authentication login
            """
            if not self.get_argument('code', False):
                print("not found")
                return self.authorize_redirect(
                    redirect_uri=self.settings['auth_redirect_uri'],
                    client_id = args.google_key if args.google_key else self.settings['google_oauth']['key'],
                    client_secret = args.google_secret if args.google_secret else self.settings['google_oauth']['secret'],
                    scope=['email', 'profile'],
                    response_type='code',
                    extra_params={'approval_prompt': 'auto'}
                )
            else:
                print("found")
                resp = await self.get_authenticated_user(
                    redirect_uri=self.settings['auth_redirect_uri'],
                    code=self.get_argument('code')
                )
                api_key = resp['access_token']
                email = jwt.decode(resp['id_token'], verify=False)['email']
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
        async def post(self):
            """Post request function for handling python notebook submissions
            """
            try:
                request = tornado.escape.json_decode(self.request.body)
                assert 'nb' in request.keys(), 'submission contains no notebook'
                assert 'api_key' in request.keys(), 'missing api key'

                notebook = request['nb']
                api_key = request['api_key']
                
                await self.submit(notebook, api_key)
            except Exception as e:
                print(e)
            self.finish()



        async def validate(self, notebook, api_key):
            """Ensures a submision is valid by checking user credentials, submission frequency, and
            validity of notebook file.

            Arguments:
                notebook (json): notebook in json form
                api_key (str): API Key generated during submission

            Returns:
                [type] -- [description]
            """
            # authenticate user with api_key
            results = await self.db.query("SELECT user_id FROM users WHERE %s=ANY(api_keys) LIMIT 1", [api_key])
            user_id = results.as_dict()['user_id'] if len(results) > 0 else None
            results.free()
            assert user_id, 'invalid api key'

            # rate limit one submission every 2 minutes
            results = await self.db.query("SELECT timestamp FROM submissions WHERE user_id=%s ORDER BY timestamp DESC LIMIT 1", [user_id])
            last_submitted = results.as_dict()['timestamp'] if len(results) > 0 else None
            results.free()

            if last_submitted:
                delta = datetime.utcnow() - last_submitted
                rate_limit = 120
                if delta.seconds < rate_limit:
                    self.write_error(429, message='Please wait {} second(s) before re-submitting.'.format(rate_limit - delta.seconds))
                    return


            # check valid Jupyter notebook
            assert all(key in notebook for key in ['metadata', 'nbformat', 'nbformat_minor', 'cells']), 'invalid Jupyter notebook'
            assert 'assignment_id' in notebook['metadata'], 'missing required metadata attribute: assignment_id'
            assignment_id = notebook['metadata']['assignment_id']
            
            results = await self.db.query("SELECT * FROM assignments WHERE assignment_id=%s LIMIT 1", [assignment_id])
            assert results, 'assignment_id {} not found on server'.format(assignment_id)
            assignment = results.as_dict()
            results.free()

            return (user_id, assignment['class_id'], assignment_id, assignment['assignment_name'])


        async def submit(self, notebook, api_key):
            """If valid submission, inserts notebook into submissions table in database and queues 
                it for grading.

            Arguments:
                notebook (json): notebook in json form
                api_key (str): API Key generated during submission
            """
            try:
                user_id, class_id, assignment_id, assignment_name = await self.validate(notebook, api_key)
            except TypeError:
                print('failed validation')
                return
            except AssertionError as e:
                print(e)
                self.write_error(400, message=e)
                return

            print("Successfully received notebook data")

            # fetch next submission id
            results = await self.db.query("SELECT nextval(pg_get_serial_sequence('submissions', 'submission_id')) as id")
            submission_id = results.as_dict()['id']
            results.free()
            print("Successfully queries submission id")

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

            print("Successfully saved nb to disk")
            
            # store submission to database
            results = await self.db.query("INSERT INTO submissions (submission_id, assignment_id, class_id, user_id, file_path, timestamp) VALUES (%s, %s, %s, %s, %s, %s)",
                                                [submission_id, assignment_id, class_id, user_id, file_path, datetime.utcnow()])
            assert results, 'submission failed'
            results.free()

            print("Successfully stored to db")

            # queue user for grading
            await user_queue.put(user_id)
            print('queued user {}'.format(user_id))

            self.write('Submission {} received.'.format(submission_id))

        @property
        def db(self):
            return self.application.db

        def write_error(self, status_code, **kwargs):
            if 'message' in kwargs:
                self.write('Submission failed: {}'.format(kwargs['message']))
            else:
                self.write('Submission failed.')


    async def grade_submission(conn):
        cursor = conn.cursor()
        
        # # This can be moved to global
        # with open("conf.yml") as f:
        #     config = yaml.safe_load(f)
        async for user in user_queue:
            # Get current user's latest submission
            cursor.execute(
                """
                SELECT user_id, submission_id, assignment_id, class_id, file_path 
                FROM submissions 
                WHERE user_id = '{}' 
                ORDER BY timestamp 
                LIMIT 1
                """.format(user)
            )
            user_record = cursor.fetchall()      
            for row in user_record:
                user_id = int(row[0])
                submission_id = float(row[1])
                assignment_id = str(row[2])
                class_id = str(row[3])
                file_path = str(row[4])
            # # Get tests directory for assignment
            # tests_path = None
            # for assignment in config["assignments"]:
            #     if assignment[assignment_id] == submission_id:
            #         tests_path = assignment["tests_path"]

            # Run grading function in a docker container
            # TODO: fix arguments below, redirect stdout/stderr
            stdout = StringIO()
            stderr = StringIO()
            try:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    df = grade_assignments(
                        tests_dir=None, 
                        notebooks_dir=os.path.split(file_path)[0], 
                        id=assignment_id, 
                        image=assignment_id,
                        debug=True
                    )
            finally:
                stdout = stdout.getvalue()
                stderr = stderr.getvalue()
                with open(os.path.join(os.path.split(file_path)[0], "GRADING_STDOUT"), "w+") as f:
                    f.write(stdout)
                with open(os.path.join(os.path.split(file_path)[0], "GRADING_STDERR"), "w+") as f:
                    f.write(stderr)
            
            df_json_str = df.to_json()

            # Insert score into submissions table
            cursor.execute("INSERT INTO submissions \
                (submission_id, assignment_id, class_id, user_id, file_path, timestamp, score) \
                VALUES (%s, %s, %s, %s, %s, %s, %s) \
                ON CONFLICT (submission_id) \
                DO UPDATE SET timestamp = %s, score = %s",
                [submission_id, assignment_id, class_id, user_id, file_path, datetime.utcnow(), df_json_str,
                datetime.utcnow(), df_json_str])
            
            # Set task done in queue
            user_queue.task_done()
        cursor.close()


    class Application(tornado.web.Application):
        def __init__(self, google_auth=True):
            """Initialize tornado server for receiving/grading submissions

            Args:
                google_auth (boolean, optional): True if google authentication is preferred. False
                    if default/personal authentication is preferred.
            """
            # TODO: these shouldn't be separate can just assume both are configured
            # if google_auth:
            # TODO: Add config file
            # with open("conf.yml") as f:
            #     config = yaml.safe_load(f)
            endpoint = args.endpoint or os.environ.get("OTTER_ENDPOINT", None)
            assert endpoint is not None, "no endpoint address provided"
            assert os.path.isdir(OTTER_SERVICE_DIR), "{} does not exist".format(OTTER_SERVICE_DIR)
            settings = dict(
                google_oauth={
                    "key": args.google_key or os.environ.get("GOOGLE_CLIENT_KEY", None), 
                    "secret": args.google_secret or os.environ.get("GOOGLE_CLIENT_SECRET", None)
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
            # else:
            #     # TODO: add personal auth
            #     handlers = [
            #         (r"/submit", SubmissionHandler),
            #         (r"/personal_auth", LoginHandler)
            #     ]
            #     tornado.web.Application.__init__(self, handlers)
            
            # Initialize database session
            self.db = queries.TornadoSession(queries.uri(
                host='localhost',
                port=5432,
                dbname='otter_db',
                user='root',
                password='root'
            ))

except ImportError:
    # don't need requirements to use otter without otter service
    MISSING_PACKAGES = True

def main(cli_args):
    if MISSING_PACKAGES:
        raise ImportError(
            "Missing some packages required for otter service. "
            "Please install all requirements at "
            "https://raw.githubusercontent.com/ucbds-infra/otter-grader/master/requirements.txt"
        )

    
    #NB_DIR = os.environ.get('NOTEBOOK_DIR')
    global conn
    global args
    global user_queue

    args = cli_args

    # TODO: add arguments below
    conn = connect_db(args.db_host, args.db_user, args.db_pass, args.db_port)
    port = 5000
    tornado.options.parse_command_line()

    # make submissions forlder
    if not os.path.isdir(OTTER_SERVICE_DIR):
        os.makedirs(os.path.join(OTTER_SERVICE_DIR))
    
    server = HTTPServer(Application(google_auth=True))
    server.listen(port)
    print("Listening on port {}".format(port))

    async def grader():
        await grade_submission(conn)

    IOLoop.current().spawn_callback(grader)
    IOLoop.current().start()
