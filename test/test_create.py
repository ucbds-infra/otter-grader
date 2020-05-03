##################################
##### Tests for otter create #####
##################################

import unittest
import os
import shutil
import datetime
from pyembedpg import PyEmbedPg
from psycopg2 import connect

from otter.service.create import *

TEST_FILES_PATH = "./test-create"

class TestBuild(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass
        
    def setUp(self):
        self.user = "testuser"
        self.password = "testpass"
        self.port = 8002
        postgres = PyEmbedPg("10.12")
        self.postgres = postgres.start(8002)
        postgres.create_user(self.user, self.password)
        postgres.create_database("otter_db", self.user)
        self.conn = connect(database="otter_db", user=self.user, password=self.password, port=self.port)
        self.cursor = self.conn.cursor()
        main(None) # Create tables

    def test_users_table(self):
        self.cursor.execute("""INSERT INTO users (api_keys, username, password)
                                VALUES ("dummykey", "dummyuser", "dummypass")""")
        self.cursor.execute("""SELECT * FROM users 
                                WHERE username = 'dummyuser' """)
        output = self.cursor.fetchall()
        assert output == [("dummykey", "dummyuser", "dummypass")], \
            "Expected {} but was {}".format([("dummykey", "dummyuser", "dummypass")], output)

    def test_submissions_table(self):
        self.cursor.execute("""INSERT INTO submissions (submission_id, assignment_id, user_id, file_path, timestamp)
                                VALUES (1234, "dummyid", 12345, "dummy/filepath", {})""".format(datetime.utcnow()))
        self.cursor.execute("""SELECT * FROM submissions 
                                WHERE submission_id = 1234 """)
        assert self.cursor.rowcount == 1, "Couldn't insert/find dummy submission"

    def test_classes_table(self):
        self.cursor.execute("""INSERT INTO classes (class_id, class_name)
                                VALUES (1234, "dummy name")""")
        self.cursor.execute("""SELECT * FROM classes 
                                WHERE class_id = 1234 """)
        assert self.cursor.rowcount == 1, "Couldn't insert/find dummy class"

    def test_assignments_table(self):
        self.cursor.execute("""INSERT INTO assignments (assignment_id, class_id, assignment_name)
                                VALUES ("dummyid", 1234, "dummy name")""")
        self.cursor.execute("""SELECT * FROM assignments 
                                WHERE assignment_id = "dummyid" """)
        output = self.cursor.fetchall()
        expected = [("dummyid", 1234, "dummy name")]
        assert output == expected, "Expected {} but was {}".format(expected, output)

    def test_user_creation(self):
        """Inserts 2 dummy username/password pairs, checks db for them,
        and removes them
        """
        user_file_path = os.path.join(TEST_FILES_PATH, "users.csv")
        create_users(user_file_path)
        # TODO: check for testusers
        self.cursor.execute("""SELECT * FROM users 
                                WHERE username = 'testuser546789' 
                                OR username = 'testuser546788'""")
        assert self.cursor.rowcount == 2
        remove_users(user_file_path)

    def cleanup(self):
        self.postgres.shutdown()