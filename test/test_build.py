##################################
##### Tests for otter build #####
##################################

import unittest
import os
import shutil

from pyembedpg import PyEmbedPg

from ..otter.service.build import *

TEST_FILES_PATH = "./test-build"

class TestBuild(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass
        
    def setUp(self):
        """does nothing
        """
        self.user = "testuser"
        self.password = "testpass"
        self.port = 8002
        postgres = PyEmbedPg("10.12")
        self.postgres = postgres.start(8002)
        postgres.create_user(self.user, self.password)
        postgres.create_database("otter_db", self.user)
        self.conn = connect(database="otter_db", user=self.user, password=self.password, port=self.port)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""INSERT INTO assignments (assignment_id, class_id, assignment_name)
                                VALUES ("dummyid", 1234, "dummy name")""")

    def test_check_assignment_id(self):
        output = check_assignment_id(["dummyid", "nonexistantid"], self.conn)
        assert output == (True, ["dummyid"])


    def test_write_class_info(self):
        class_id = write_class_info("test class", self.conn)
        self.cursor.execute("""SELECT * FROM classes
                                WHERE class_id = {}""".format(class_id))
        assert self.cursor.rowcount == 1, "Couldn't find inserted class"


    def test_write_assignment_info(self):
        write_assignment_info("dummy_aid", 1234, "dummy class name", self.conn)
        write_assignment_info("dummy_aid2", 2345, "dummy class name 2", self.conn)
        self.cursor.execute("""SELECT * FROM classes WHERE class_id = 2345""")
        assert self.cursor.rowcount == 1, "Couldn't find inserted assignment information for dummy_aid2"

    def test_docker(self):
        main("./test-build/conf.yml") # Function has built-in assert statement for error-checking
        

        