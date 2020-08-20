############################################
##### Tests for otter service start.py #####
############################################

import os
import testing.postgresql
import otter.service.create
import queries
import json

from unittest import mock
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase, gen_test
from tornado.web import Application
from tornado.ioloop import IOLoop
from asyncio import CancelledError
from datetime import datetime, timedelta
from psycopg2 import connect, extensions
from collections import namedtuple

from otter.argparser import get_parser
from otter.service import start
from otter.service.create import main as create

from .. import TestCase

TEST_FILES_PATH = "test/test_service/test-start/"

parser = get_parser()

class TestServiceAuthHandlers(AsyncHTTPTestCase, TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # setup test database
        cls.postgresql = testing.postgresql.Postgresql()
        cls.conn = connect(**cls.postgresql.dsn())
        cls.conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        start.CONN = cls.conn

        args = parser.parse_args(["service", "create"])
        args.func = create
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
                    (r"/auth/google", start.GoogleOAuth2LoginHandler),
                    (r"/auth/callback", start.GoogleOAuth2LoginHandler),
                    (r"/auth", start.LoginHandler)
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
    
    @mock.patch.object(start.GoogleOAuth2LoginHandler, 'get_authenticated_user', new_callable=GetAuthenticatedUserMock)
    @mock.patch.object(start.GoogleOAuth2LoginHandler, 'get_argument', return_value=True, autospec=True)
    @mock.patch.object(start.jwt, 'decode', return_value={'email': 'user3@example.com'}, autospec=True)
    @mock.patch.object(start.os, 'urandom', autospec=True)
    def test_google_auth(self, mock_urandom, mock_jwt_decode, mock_getarg, mock_get_user):
        mock_urandom.side_effect = [str(i).encode() for i in range(4)]
        resp1 = self.fetch('/auth/google')
        resp2 = self.fetch('/auth/google')
        self.assertEqual(resp1.code, 200, resp1.body)
        self.assertEqual(resp2.code, 200, resp2.body)

        self.cursor.execute("SELECT * FROM users")

        self.cursor.execute(
            """
            SELECT * FROM users WHERE email = 'user3@example.com'
            """
        )
        results = self.cursor.fetchall()

        # check database has the expected api keys after two auth requests
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], ['30', '31'])

    @mock.patch('os.urandom', autospec=True)
    @mock.patch('hashlib.sha256', autospec=True)
    def test_auth_fail(self, mock_hash, mock_urandom):
        mock_hash.side_effect = self.hash_side_effect
        mock_urandom.side_effect = [str(i).encode() for i in range(4)]

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


class TestServiceSubmissionHandler(AsyncHTTPTestCase, TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # set up test database
        cls.postgresql = testing.postgresql.Postgresql()
        cls.conn = connect(**cls.postgresql.dsn())
        cls.conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        start.CONN = cls.conn
        # start.ARGS = namedtuple("Args", )

        args = parser.parse_args(["service", "create"])
        args.func = create
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
                handlers = [(r"/submit", start.SubmissionHandler)]
                Application.__init__(self, handlers, **settings)
                self.db = queries.TornadoSession(queries.uri(**dsn))

        return SubmissionApplication()

    def test_submission_fail(self):
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
        self.assertIn('invalid API key', resp2.body.decode("utf-8"))
        self.assertIn('invalid Jupyter notebook', resp3.body.decode("utf-8"))

    def test_one_submission(self):
        self.reset_timestamps()
        self.clear_submissions()
        with open(TEST_FILES_PATH + 'notebooks/valid/passesAll.ipynb') as f:
            data = json.load(f)
        data["metadata"]["assignment_id"] = "1"
        data["metadata"]["class_id"] = "1"

        request = {'api_key': 'key1', 'nb': data}
        resp1 = self.fetch('/submit', method='POST', body=json.dumps(request))

        self.assertEqual(resp1.code, 200)

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
        data["metadata"]["assignment_id"] = "1"
        data["metadata"]["class_id"] = "1"
        
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

        # schema:
        #   0 submission_id SERIAL PRIMARY KEY,
        #   1 assignment_id TEXT NOT NULL,
        #   2 class_id TEXT NOT NULL,
        #   3 user_id INTEGER REFERENCES users(user_id) NOT NULL,
        #   4 file_path TEXT NOT NULL,
        #   5 timestamp TIMESTAMP NOT NULL,
        #   6 score JSONB,

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
        expected = [('1', '1', 1), ('1', '1', 2), ('1', '1', 3)]
        self.assertEqual(sorted(submissions), sorted(expected))

        # check notebooks written to disk
        for row in results:
            self.assertTrue(os.path.isfile(row[4]))
            with open(TEST_FILES_PATH + 'notebooks/valid/passesAll.ipynb') as f:
                expected_nb = json.load(f)
            expected_nb["metadata"]["assignment_id"] = "1"
            expected_nb["metadata"]["class_id"] = "1"
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

    # @mock.patch.object(start, 'grade_assignments', autospec=True)
    # @mock.patch('io.StringIO', return_value='', autospec=True)
    # @gen_test(timeout=1)
    # async def test_grade(self, mock_io, mock_grade):
    #     import pandas as pd
    #     import re

    #     mock_scores = [pd.DataFrame(['score1']),
    #                    pd.DataFrame(['score2']),
    #                    pd.DataFrame(['score3']),
    #                    pd.DataFrame(['score4']),
    #                    pd.DataFrame(['score5'])]
    #     mock_grade.side_effect = mock_scores
    #     timestamps = [datetime.utcnow() - timedelta(days=x) for x in range(5)]
    #     for submission in [1, 2, 3, 4, 5]:
    #         start.SUBMISSION_QUEUE.put(submission)

    #     self.cursor.execute(
    #         """
    #         INSERT INTO submissions (submission_id, assignment_id, class_id, user_id, file_path, timestamp)
    #         VALUES (5, '1', 1, 2, ' ', %s),
    #                (4, '1', 1, 1, ' ', %s),
    #                (3, '1', 1, 3, ' ', %s),
    #                (2, '1', 1, 2, ' ', %s),
    #                (1, '1', 1, 1, ' ', %s)
    #         """,
    #         timestamps
    #     )

    #     # # set conn so start has access to it
    #     # start.CONN = self.conn

    #     # tornado test will timeout start_grading_queue once SUBMISSION_QUEUE is depleted
    #     with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
    #         try:
    #             m = mock.mock_open()
    #             with mock.patch.object(start.stdio_proxy, "redirect_stdout", m):
    #                 with mock.patch.object(start.stdio_proxy, "redirect_stderr", m):
    #                     await start.start_grading_queue(shutdown=True)
    #         except CancelledError:
    #             pass

    #     self.cursor.execute(
    #         """
    #         SELECT * FROM submissions
    #         WHERE user_id = ANY ('{1,2,3}'::int[])
    #         ORDER BY timestamp ASC
    #         """
    #     )
    #     results = self.cursor.fetchall()

    #     # check scores are updated in submissions table
    #     scores = [re.search('score.', json.dumps(row[6], default=lambda o: "not serializable"), flags=re.MULTILINE).group(0) for row in results]
    #     expected_scores = [re.search('score.', score.to_json()).group(0) for score in mock_scores]
    #     self.assertCountEqual(expected_scores, scores)

    @classmethod
    def tearDownClass(cls):
        cls.cursor.close()
        cls.conn.close()
        cls.postgresql.stop()
        if os.path.exists('test_submissions'):
            os.system("rm -r test_submissions")
        if os.path.exists("GRADING_STDOUT"):
            os.system("rm GRADING_STDOUT")
        if os.path.exists("GRADING_STDERR"):
            os.system("rm GRADING_STDERR")
