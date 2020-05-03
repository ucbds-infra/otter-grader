############################################
##### Tests for otter service start.py #####
############################################

import os
import testing.postgresql
import otter.service.create
import queries
import json

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from unittest import mock
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase, gen_test
from tornado.web import Application
from tornado.ioloop import IOLoop
from asyncio import CancelledError
from datetime import datetime, timedelta
from psycopg2 import connect, extensions

from otter.service.start import GoogleOAuth2LoginHandler, LoginHandler, SubmissionHandler, grade_submission, user_queue

TEST_FILES_PATH = "test/test_service/test-start/"

parser = None
with open("bin/otter") as f:
    exec(f.read())

class TestServiceAuthHandlers(AsyncHTTPTestCase):

    @classmethod
    def setUpClass(cls):
        # setup test database
        cls.postgresql = testing.postgresql.Postgresql()
        cls.conn = connect(**cls.postgresql.dsn())
        cls.conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        args = parser.parse_args(["service", "create"])
        args.func(args, conn=cls.conn, close_conn=False)

        cls.cursor = cls.conn.cursor()

        queries = [
            '''
            INSERT INTO users (username, password)
            VALUES ('user1', 'pass1'), ('user2', 'pass2')
            '''
        ]
        for query in queries:
            cls.cursor.execute(query)

    def get_app(self):
        dsn = self.postgresql.dsn()
        dsn['dbname'] = dsn.pop('database')

        class AuthApplication(Application):
            def __init__(self):
                settings = dict(
                    auth_redirect_uri=None
                )
                handlers = [
                    (r"/auth/google", GoogleOAuth2LoginHandler),
                    (r"/auth/callback", GoogleOAuth2LoginHandler),
                    (r"/auth", LoginHandler)
                ]
                Application.__init__(self, handlers, **settings)
                self.db = queries.TornadoSession(queries.uri(**dsn))

        return AuthApplication()

    def hash_side_effect(self, input):
        class HashMock():
            def __init__(self, value):
                self.value = value  

            def hexdigest(self):
                return self.value

        return HashMock(input.decode())

    class GetAuthenticatedUserMock(mock.MagicMock):
        def __init__(self, *args, **kwargs):
            super(mock.MagicMock, self).__init__(*args, **kwargs)
            self._keys = iter([{'access_token': 'key1', 'id_token': ''},
                               {'access_token': 'key2', 'id_token': ''}])

        async def __call__(self, *args, **kwargs):
            return next(self._keys)
    
    @mock.patch.object(GoogleOAuth2LoginHandler, 'get_authenticated_user', new_callable=GetAuthenticatedUserMock)
    @mock.patch.object(GoogleOAuth2LoginHandler, 'get_argument', return_value=True, autospec=True)
    @mock.patch('jwt.decode', return_value={'email': 'user3@example.com'}, autospec=True)
    def test_google_auth(self, mock_getarg, mock_get_user, mock_jwt_decode):
        with redirect_stdout(StringIO()):
            resp1 = self.fetch('/auth/google')
            resp2 = self.fetch('/auth/google')
        self.assertEqual(resp1.code, 200)
        self.assertEqual(resp2.code, 200)

        self.cursor.execute(
            """
            SELECT * FROM users WHERE email = 'user3@example.com'
            """
        )
        results = self.cursor.fetchall()

        # check database has the expected api keys after two auth requests
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], ['key1', 'key2'])

    @mock.patch('os.urandom', autospec=True)
    @mock.patch('hashlib.sha256', autospec=True)
    def test_auth_fail(self, mock_hash, mock_urandom):
        mock_hash.side_effect = self.hash_side_effect
        mock_urandom.side_effect = [str(i).encode() for i in range(4)]

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            resp1 = self.fetch('/auth?username={}&password={}'.format('user1', 'invalid_pass'))
            resp2 = self.fetch('/auth?username={}&password={}'.format('user2', 'invalid_pass'))
            resp3 = self.fetch('/auth?username={}&password={}'.format('invalid_user', 'pass1'))
        self.assertEqual(resp1.code, 401)
        self.assertEqual(resp2.code, 401)
        self.assertEqual(resp3.code, 401)

        self.cursor.execute(
            """
            SELECT * FROM users WHERE username IN ('user1', 'user2') ORDER BY username ASC
            """
        )
        results = self.cursor.fetchall()

        # check api key arrays for user1 and user2 are empty and unchanged
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][1], None)
        self.assertEqual(results[1][1], None)

    @mock.patch('os.urandom', autospec=True)
    @mock.patch('hashlib.sha256', autospec=True)
    def test_auth_success(self, mock_hash, mock_urandom):
        mock_hash.side_effect = self.hash_side_effect
        mock_urandom.side_effect = [str(i).encode() for i in range(4)]

        resp1 = self.fetch('/auth?username={}&password={}'.format('user1', 'pass1'))
        resp2 = self.fetch('/auth?username={}&password={}'.format('user2', 'pass2'))
        resp3 = self.fetch('/auth?username={}&password={}'.format('user1', 'pass1'))
        resp4 = self.fetch('/auth?username={}&password={}'.format('user2', 'pass2'))
        self.assertEqual(resp1.code, 200)
        self.assertEqual(resp2.code, 200)
        self.assertEqual(resp3.code, 200)
        self.assertEqual(resp4.code, 200)

        self.cursor.execute(
            """
            SELECT * FROM users WHERE username IN ('user1', 'user2') ORDER BY username ASC
            """
        )
        results = self.cursor.fetchall()

        # check api keys for user1 and user2 are as expected
        self.assertEqual(results[0][1], ['30', '32'])
        self.assertEqual(results[1][1], ['31', '33'])

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.postgresql.stop()


class TestServiceSubmissionHandler(AsyncHTTPTestCase):

    @classmethod
    def setUpClass(cls):
        # set up test database
        cls.postgresql = testing.postgresql.Postgresql()
        cls.conn = connect(**cls.postgresql.dsn())
        cls.conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        args = parser.parse_args(["service", "create"])
        args.func(args, conn=cls.conn, close_conn=False)

        cls.cursor = cls.conn.cursor()

        queries = [
            '''
            INSERT INTO users (user_id, username, password, api_keys)
            VALUES (1, 'user1', 'pass1', ARRAY['key1']),
                   (2, 'user2', 'pass2', ARRAY['key2', 'key3']),
                   (3, 'user3', 'pass3', ARRAY['key4'])
            ''',
            '''
            INSERT INTO classes (class_id, class_name)
            VALUES (1, 'test_class')
            ''',
            '''
            INSERT INTO assignments (assignment_id, class_id, assignment_name)
            VALUES (1, 1, 'assignment1')
            '''
        ]
        for query in queries:
            cls.cursor.execute(query)

    def get_app(self):
        dsn = self.postgresql.dsn()
        dsn['dbname'] = dsn.pop('database')

        class SubmissionApplication(Application):
            def __init__(self):
                settings = dict(notebook_dir="test_submissions")
                handlers = [(r"/submit", SubmissionHandler)]
                Application.__init__(self, handlers, **settings)
                self.db = queries.TornadoSession(queries.uri(**dsn))

        return SubmissionApplication()

    def test_submission_fail(self):
        with redirect_stdout(StringIO()):
            self.reset_timestamps()
            with open(TEST_FILES_PATH + 'notebooks/invalid/passesAll.ipynb') as f:
                data = json.load(f)
            request = {'api_key': 'key1', 'nb': data}
            resp1 = self.fetch('/submit', method='POST', body=json.dumps(request))

            self.reset_timestamps()
            with open(TEST_FILES_PATH + 'notebooks/valid/passesAll.ipynb') as f:
                data = json.load(f)
            request = {'api_key': 'invalid_key', 'nb': data}
            resp2 = self.fetch('/submit', method='POST', body=json.dumps(request))

            self.reset_timestamps()
            request = {'api_key': 'key1', 'nb': {}}
            resp3 = self.fetch('/submit', method='POST', body=json.dumps(request))

        self.assertEqual(resp1.code, 200)
        self.assertEqual(resp2.code, 200)
        self.assertEqual(resp3.code, 200)
        self.assertIn('missing required metadata attribute', resp1.body.decode("utf-8"))
        self.assertIn('invalid api key', resp2.body.decode("utf-8"))
        self.assertIn('invalid Jupyter notebook', resp3.body.decode("utf-8"))

    def test_one_submission(self):
        self.reset_timestamps()
        self.clear_submissions()
        with redirect_stdout(StringIO()):
            with open(TEST_FILES_PATH + 'notebooks/valid/passesAll.ipynb') as f:
                data = json.load(f)
            request = {'api_key': 'key1', 'nb': data}
            resp1 = self.fetch('/submit', method='POST', body=json.dumps(request))
        self.assertEqual(resp1.code, 200)
        
        # check user queue
        self.assertEqual(user_queue.qsize(), 1)
        self.assertEqual(user_queue.get_nowait(), 1)

        self.cursor.execute(
            """
            SELECT * FROM submissions WHERE user_id = 1 ORDER BY user_id ASC
            """
        )
        results = self.cursor.fetchall()

        # check submission saved to database and disk
        self.assertEqual(len(results), 1)
        submission_path = results[0][4]
        self.assertTrue(os.path.isfile(submission_path))

    def test_multiple_submissions(self):
        self.reset_timestamps()
        self.clear_submissions()

        with open(TEST_FILES_PATH + 'notebooks/valid/passesAll.ipynb') as f:
            data = json.load(f)
        
        with redirect_stdout(StringIO()):
            user1_request = {'api_key': 'key1', 'nb': data}
            resp1 = self.fetch('/submit', method='POST', body=json.dumps(user1_request))
            user3_request = {'api_key': 'key4', 'nb': data}
            resp2 = self.fetch('/submit', method='POST', body=json.dumps(user3_request))
            user2_request = {'api_key': 'key2', 'nb': data}
            resp4 = self.fetch('/submit', method='POST', body=json.dumps(user2_request))
            self.reset_timestamps()
            resp3 = self.fetch('/submit', method='POST', body=json.dumps(user3_request))
            user2_request = {'api_key': 'key3', 'nb': data}
            resp5 = self.fetch('/submit', method='POST', body=json.dumps(user2_request))

        self.assertEqual(resp1.code, 200)
        self.assertEqual(resp2.code, 200)
        self.assertEqual(resp4.code, 200)
        self.assertEqual(resp3.code, 200)
        self.assertEqual(resp5.code, 200)

        # check user queue
        self.assertEqual(user_queue.qsize(), 5)
        userq = [user_queue.get_nowait() for _ in range(5)]
        self.assertEqual(userq, [1, 3, 2, 3, 2])

        self.cursor.execute(
            """
            SELECT * FROM submissions
            WHERE user_id = ANY ('{1,2,3}'::int[])
            ORDER BY user_id ASC
            """
        )
        results = self.cursor.fetchall()
        
        # check submissions table contains expected entries (assignment_id, user_id)
        submissions = [row[1:4] for row in results]
        expected = [('1', 1, 1), ('1', 1, 2), ('1', 1, 2), ('1', 1, 3), ('1', 1, 3)]
        self.assertEqual(sorted(submissions), sorted(expected))

        # check notebooks written to disk
        for row in results:
            self.assertTrue(os.path.isfile(row[4]))
            with open(TEST_FILES_PATH + 'notebooks/valid/passesAll.ipynb') as f:
                expected_nb = json.load(f)
            with open(row[4]) as f:
                saved_nb = json.load(f)
            self.assertEqual(expected_nb, saved_nb)

    # helper to bypass request timeouts
    def reset_timestamps(self):
        self.cursor.execute(
            """
            UPDATE submissions SET timestamp = (%s)
            """,
            [datetime.utcnow() - timedelta(seconds=121)]
        )

    # clear submissions table
    def clear_submissions(self):
        self.cursor.execute(
            """
            TRUNCATE submissions
            """
        )

    @mock.patch('otter.service.start.grade_assignments', autospec=True)
    @mock.patch('io.StringIO', return_value='', autospec=True)
    @gen_test(timeout=1)
    async def test_grade(self, mock_io, mock_grade):
        import pandas as pd
        import re

        mock_scores = [pd.DataFrame(['score1']),
                       pd.DataFrame(['score2']),
                       pd.DataFrame(['score3']),
                       pd.DataFrame(['score4']),
                       pd.DataFrame(['score5'])]
        mock_grade.side_effect = mock_scores
        timestamps = [datetime.utcnow() - timedelta(days=x) for x in range(5)]
        for user in [1, 2, 3, 1, 2]:
            user_queue.put(user)

        self.cursor.execute(
            """
            INSERT INTO submissions (submission_id, assignment_id, class_id, user_id, file_path, timestamp)
            VALUES (5, '1', 1, 2, ' ', %s),
                   (4, '1', 1, 1, ' ', %s),
                   (3, '1', 1, 3, ' ', %s),
                   (2, '1', 1, 2, ' ', %s),
                   (1, '1', 1, 1, ' ', %s)
            """,
            timestamps
        )

        # tornado test will timeout grade() once user_queue is depleted
        try:
            await grade_submission(self.conn)
        except CancelledError:
            pass

        self.cursor.execute(
            """
            SELECT * FROM submissions
            WHERE user_id = ANY ('{1,2,3}'::int[])
            ORDER BY timestamp ASC
            """
        )
        results = self.cursor.fetchall()

        # check scores are updated in submissions table
        scores = [re.search('score.', str(row[6])).group(0) for row in results]
        expected_scores = [re.search('score.', score.to_json()).group(0) for score in mock_scores]
        self.assertEqual(expected_scores, scores)

    @classmethod
    def tearDownClass(cls):
        cls.cursor.close()
        cls.conn.close()
        cls.postgresql.stop()
        if os.path.exists('test_submissions'):
            os.system("rm -r test_submissions")
        if os.path.exists("GRADING_STDOUT"):
            os.system("rm GRADING_STDOUT")
