##################################
##### Tests for otter create #####
##################################

import unittest
import os
import shutil
import datetime
import testing.postgresql

from unittest import mock
from psycopg2 import connect, extensions
from psycopg2.errors import DuplicateTable

from otter.argparser import get_parser
from otter.service.create import create_users, remove_users
from otter.service.create import main as create

from .. import TestCase

TEST_FILES_PATH = "test/test_service/test-create/"

parser = get_parser()

class TestCreate(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        cls.postgresql = testing.postgresql.Postgresql()
        cls.conn = connect(**cls.postgresql.dsn())
        cls.conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        args = parser.parse_args(["service", "create"])
        args.func = create
        args.func(args, conn=cls.conn)

        cls.conn = connect(**cls.postgresql.dsn())
        cls.conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cls.cursor = cls.conn.cursor()
    

    def test_tables(self):
        # users table
        self.cursor.execute("""INSERT INTO users (user_id, api_keys, username, password)
                                VALUES (1234, '{{dummykey}}', 'dummyuser', 'dummypass')""")
        self.cursor.execute("""SELECT * FROM users 
                                WHERE username = 'dummyuser' """)
        output = self.cursor.fetchall()
        assert output == [(1234, [['dummykey']], 'dummyuser', 'dummypass', None)], \
            "Expected {} but was {}".format([(1234, [['dummykey']], 'dummyuser', 'dummypass', None)], output)

        # classes table
        self.cursor.execute("""INSERT INTO classes (class_id, class_name)
                                VALUES (1234, 'dummy name')""")
        self.cursor.execute("""SELECT * FROM classes 
                                WHERE class_id = '1234' """)
        assert self.cursor.rowcount == 1, "Couldn't insert/find dummy class"

        # assignments table
        self.cursor.execute("""INSERT INTO assignments (assignment_id, class_id, assignment_name)
                                VALUES ('dummyid', '1234', 'dummy name')""")
        self.cursor.execute("""SELECT * FROM assignments 
                                WHERE assignment_id = 'dummyid' """)
        output = self.cursor.fetchall()
        expected = [("dummyid", '1234', "dummy name", None)]
        assert output == expected, "Expected {} but was {}".format(expected, output)

        # submissions table
        self.cursor.execute("""INSERT INTO submissions (submission_id, assignment_id, class_id, user_id, file_path, timestamp)
                                VALUES (1234, 'dummyid', 1234, 1234, 'dummy/filepath', '{}')""".format(datetime.datetime.utcnow()))
        self.cursor.execute("""SELECT * FROM submissions 
                                WHERE submission_id = 1234 """)
        assert self.cursor.rowcount == 1, "Couldn't insert/find dummy submission"
        

    def test_user_creation(self):
        """Inserts 2 dummy username/password pairs, checks db for them,
        and removes them
        """
        user_file_path = os.path.join(TEST_FILES_PATH, "users.csv")
        create_users(user_file_path, conn=self.conn)
        # TODO: check for testusers
        self.cursor.execute("""SELECT * FROM users 
                                WHERE username = 'testuser546789' 
                                OR username = 'testuser546788'""")
        assert self.cursor.rowcount == 2, "Expected 2 rows but was {}".format(self.cursor.rowcount)
        remove_users(user_file_path, conn=self.conn)

    @classmethod
    def tearDownClass(cls):
        cls.cursor.close()
        cls.conn.close()
        cls.postgresql.stop()
