##################################
##### Tests for otter notebook #####
##################################

import unittest
import sys
import os
import shutil
import subprocess
<<<<<<< HEAD
import json
import requests

=======
import responses
>>>>>>> df8bdbea5af4799f98e477ec7eb05182858aec85


from subprocess import PIPE
from glob import glob
from unittest.mock import patch
from unittest import mock

import notebook
from otter import Notebook
from otter.check.logs import LogEntry, EventType, Log
from otter.check.notebook import _OTTER_LOG_FILENAME
from otter.check import notebook

from . import TestCase

TEST_FILES_PATH = "test/test-notebook/"


# functions used in one of the tests below
def square(x):
    return x ** 2


def negate(x):
    return not x

<<<<<<< HEAD
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.text = json_data
            self.status_code = status_code


        def json(self):
            return self.json_data


    if args[0] == "http://some.url/auth/google":
        return MockResponse({"text": "value1"}, 200)
    elif args[0] == "http://some.url/submit":
        return MockResponse({"text": "this is the fake post response"}, 200)

    return MockResponse(None, 404)


def mock_auth_get():
    class AuthResponse:
        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

        def content(self):
            print('hssdhfs')
            return self

        def decode(self, type):
            print('aaaawe')
            return "fakekey"

    str = "fakekey"
    content = str.encode("utf-8", "strict")
    response = AuthResponse(content, 2)

    return response


=======
>>>>>>> df8bdbea5af4799f98e477ec7eb05182858aec85

class TestNotebook(TestCase):
    """
    Test cases for the ``Notebook`` class
    """

    #from otter.check import notebook
    #notebook._API_KEY = none
    # def setUp(self):
    #     super().setUp()
    #     global _API_KEY
    #     _API_KEY = None
    #
    #     print('hi')



    """
    Checks that the otter.Notebook class init works correctly
    """

    def test_init_1(self):
        
        """
        otter_configs exists, _service_enabled = True, auth exists
        """

        # Set up otter_config file
        variables = {
            "arr": "numpy.ndarray"
        }

        config = {
            "notebook": "hw00.ipynb",
            "endpoint": "http://some.url", # dont include this when testing service enabled stuff
            "assignment_id": "hw00",
            "class_id": "some_class",
            "auth": "google",
            "save_environment": False,
            "ignore_modules": [],
            "variables": variables
            }

        # Make new otter config file, put it in direcotry
        f = open("demofile2.otter", "a")
        f.write(json.dumps(config))
        f.close()

        # Instance of Notebook class
        grader = Notebook(TEST_FILES_PATH + "tests")


        # Delete otter_config file
        if os.path.exists("demofile2.otter"):
            os.remove("demofile2.otter")
        else:
            print("The file does not exist")


        for q_path in glob(TEST_FILES_PATH + "tests/*.py"):
            q = os.path.split(q_path)[1][:-3]

            # Checks to make sure Notebook took in the config file correctly
            self.assertEqual(grader._ignore_modules, config['ignore_modules'], "Test {} init (ignore modules) failed".format(q))
            self.assertEqual(grader._service_enabled, True, "Test {} init (service enabled) failed".format(q))
            self.assertEqual(grader._vars_to_store, config['variables'], "Test {} init (variables) failed".format(q))
            self.assertEqual(grader._notebook, config['notebook'], "Test {} init (notebook) failed".format(q))
            self.assertEqual(grader._config['auth'], config['auth'], "Test {} init (auth) failed".format(q))
            self.assertEqual(grader._google_auth_url, "http://some.url/auth/google", "Test {} init (google auth url) failed".format(q))
            self.assertEqual(grader._default_auth_url, "http://some.url/auth", "Test {} init (default auth url) failed".format(q))
            self.assertEqual(grader._submit_url, "http://some.url/submit", "Test {} init (submit url) failed".format(q))





    def test_init_2(self):

        """
        otter_configs exists, _service_enabled = True, auth does not exist
        """

        variables = {
            "arr": "numpy.ndarray"
        }

        config2 = {
            "notebook": "hw00.ipynb",
            "endpoint": "http://some.url", # dont include this when testing service enabled stuff
            "assignment_id": "hw00",
            "class_id": "some_class",
            "save_environment": False,
            "ignore_modules": [],
            "variables": variables
            }

        # Make new otter config file, put it in direcotry
        f = open("demofile3.otter", "a")
        f.write(json.dumps(config2))
        f.close()

        # Instance of Notebook class
        grader = Notebook(TEST_FILES_PATH + "tests")

        # Delete otter_config file
        if os.path.exists("demofile3.otter"):
            os.remove("demofile3.otter")
        else:
            print("The file does not exist")


        for q_path in glob(TEST_FILES_PATH + "tests/*.py"):
            q = os.path.split(q_path)[1][:-3]
            self.assertEqual(grader._ignore_modules, config2['ignore_modules'], "Test {} init (ignore modules) failed".format(q))
            self.assertEqual(grader._service_enabled, True, "Test {} init (service enabled) failed".format(q))
            self.assertEqual(grader._vars_to_store, config2['variables'], "Test {} init (variables) failed".format(q))
            self.assertEqual(grader._notebook, config2['notebook'], "Test {} init (notebook) failed".format(q))
            self.assertEqual(grader._config['auth'], 'google', "Test {} init (auth) failed".format(q))
            self.assertEqual(grader._google_auth_url, "http://some.url/auth/google", "Test {} init (google auth url) failed".format(q))
            self.assertEqual(grader._default_auth_url, "http://some.url/auth", "Test {} init (default auth url) failed".format(q))
            self.assertEqual(grader._submit_url, "http://some.url/submit", "Test {} init (submit url) failed".format(q))



    def test_init_3(self):

        """
        More than 1 otter_config
        """

        variables = {
            "arr": "numpy.ndarray"
        }

        config2 = {
            "notebook": "hw00.ipynb",
            "endpoint": "http://some.url", # dont include this when testing service enabled stuff
            "assignment_id": "hw00",
            "class_id": "some_class",
            "save_environment": False,
            "ignore_modules": [],
            "variables": variables
            }

        f = open("demofile4.otter", "a")
        f.write(json.dumps(config2))
        f.close()

        f2 = open("demofile5.otter", "a")
        f2.write(json.dumps(config2))
        f2.close()

        # Instance of Notebook class, should throw Exception
        with self.assertRaises(Exception):
            Notebook(TEST_FILES_PATH + "tests")

        # Delete otter_config file
        if os.path.exists("demofile4.otter"):
            os.remove("demofile4.otter")
            os.remove("demofile5.otter")
        else:
            print("The file does not exist")




    """
    These tests check to see that auth correctly authorizes a student, based off
    the student-inputted config file
    """


    @mock.patch('builtins.input', return_value='fakekey')
    def test_auth_1(self, mock_get):

        """
        otter_configs exists, _service_enabled = True, auth exists but incorrect
        and should throw an exception (case where auth does not exist covered in init)
        """

        variables = {
            "arr": "numpy.ndarray"
        }


        config = {
            "notebook": "hw00.ipynb",
            "endpoint": "http://some.url", # dont include this when testing service enabled stuff
            "assignment_id": "hw00",
            "class_id": "some_class",
            "auth": "googe",
            "save_environment": False,
            "ignore_modules": [],
            "variables": variables
            }

        # Make new otter config file, put it in direcotry
        f = open("demofile6.otter", "a")
        f.write(json.dumps(config))
        f.close()

        # Instance of Notebook class
        with self.assertRaises(Exception):
            Notebook(TEST_FILES_PATH + "tests")

        # Delete otter_config file
        if os.path.exists("demofile6.otter"):
            os.remove("demofile6.otter")
        else:
            print("The file does not exist")





    @mock.patch('builtins.input')
    def test_auth_2(self, mock_input):

        """
        otter_configs exists, _service_enabled = True, auth is google
        and not should throw an exception (goes into google if statement)
        """

        # set up mock input
        mock_input.return_value = "fakekey"

        variables = {
            "arr": "numpy.ndarray"
        }

        config = {
            "notebook": "hw00.ipynb",
            "endpoint": "http://some.url", # dont include this when testing service enabled stuff
            "assignment_id": "hw00",
            "class_id": "some_class",
            "auth": "google",
            "save_environment": False,
            "ignore_modules": [],
            "variables": variables
            }

        # Make new otter config file, put it in direcotry
        f = open("demofile6.otter", "a")
        f.write(json.dumps(config))
        f.close()

        # Instance of Notebook class
        grader = Notebook(TEST_FILES_PATH + "tests")

        self.assertEqual(grader._api_key, "fakekey")

        # Delete otter_config file
        if os.path.exists("demofile6.otter"):
            os.remove("demofile6.otter")
        else:
            print("The file does not exist")





    @mock.patch('builtins.input')
    def test_auth_3(self, mock_input):

        """
        otter_configs exists, _service_enabled = True, auth is automatically set
        and not should throw an exception, _API_KEY exists from test_auth_2
        """

        # set up mock input
        mock_input.return_value='fake input'


        variables = {
            "arr": "numpy.ndarray"
        }

        config = {
            "notebook": "hw00.ipynb",
            "endpoint": "http://some.url", # dont include this when testing service enabled stuff
            "assignment_id": "hw00",
            "class_id": "some_class",
            "auth": "default",
            "save_environment": False,
            "ignore_modules": [],
            "variables": variables
            }

        # Make new otter config file, put it in direcotry
        f = open("demofile6.otter", "a")
        f.write(json.dumps(config))
        f.close()

        # Instance of Notebook class
        grader = Notebook(TEST_FILES_PATH + "tests")

        self.assertEqual(grader._api_key, "fakekey")

        # Delete otter_config file
        if os.path.exists("demofile6.otter"):
            os.remove("demofile6.otter")
        else:
            print("The file does not exist")



    @mock.patch('otter.check.notebook.requests.get')
    @mock.patch('otter.check.notebook.getpass')
    @mock.patch('otter.check.notebook.input')
    def test_auth_4(self, mock_input, mock_pass, mock_get):

        """
        otter_configs exists, _service_enabled = True, auth is automatically set
        and not should throw an exception, _API_KEY exists from test_auth_2
        """

        # sets api_key to none to avoid first if statement in notebook.auth()
        notebook._API_KEY = None

        # sets up methods to mock
        mock_get.return_value = mock_auth_get()
        mock_pass.return_value = "fake pass"
        mock_input.return_value = "fake input"

        variables = {
            "arr": "numpy.ndarray"
        }


        config = {
            "notebook": "hw00.ipynb",
            "endpoint": "http://some.url",
            "assignment_id": "hw00",
            "class_id": "some_class",
            "auth": "default",
            "save_environment": False,
            "ignore_modules": [],
            "variables": variables
            }

        # Make new otter config file, put it in direcotry
        f = open("demofile6.otter", "a")
        f.write(json.dumps(config))
        f.close()

        # Instance of Notebook class
        grader = Notebook(TEST_FILES_PATH + "tests")

        self.assertEqual(grader._api_key, "fakekey")


        if os.path.exists("demofile6.otter"):
            os.remove("demofile6.otter")
        else:
            print("The file does not exist")




    """
    These tests check to see that notebook.submit() correctly posts an assignment
    """

    def test_submit_1(self):

        """
        _service_enabled = False, should raise an exception
        """

        variables = {
            "arr": "numpy.ndarray"
        }

        # Instance of Notebook class
        with self.assertRaises(Exception):
            grader = Notebook(TEST_FILES_PATH + "tests")
            grader.submit()


    @mock.patch('otter.check.notebook.requests.post', side_effect=mocked_requests_get)
    def test_submit_2(self, mock_get):

        """
        otter_configs exists, _service_enabled = True, should go into auth and run as it should
        """

        variables = {
            "arr": "numpy.ndarray"
        }

        config = {
            "notebook": "hw00.ipynb",
            "assignment_id": "hw00",
            "class_id": "some_class",
            "auth": "google",
            "save_environment": False,
            "ignore_modules": [],
            "variables": variables,
            "endpoint": "http://some.url",
                    }

        f = open("demofile6.otter", "a")
        f.write(json.dumps(config))
        f.close()


        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.submit()

        #check to see if the right file was used
        args, kwargs = mock_get.call_args
        self.assertEqual(config['endpoint'] + '/submit', args[0])




        # Delete otter_config file
        if os.path.exists("demofile6.otter"):
            os.remove("demofile6.otter")
        else:
            print("The file does not exist")















    @mock.patch('builtins.input', return_value='fakekey')
    def test_check(self, mock_input):
        """
        Checks that the otter.Notebook class works correctly
        """
        notebook._API_KEY = 'fakekey'

        # i1 = Notebook(TEST_FILES_PATH + "tests") #bypass setup
        grader = Notebook(TEST_FILES_PATH + "tests")

        def square(x):
            return x ** 2

        def negate(x):
            return not x

        global_env = {
            "square": square,
            "negate": negate
        }

        for q_path in glob(TEST_FILES_PATH + "tests/*.py"):
            q = os.path.split(q_path)[1][:-3]
            result = grader.check(q, global_env=global_env)
            if q != "q2":
                self.assertEqual(result.grade, 1, "Test {} failed".format(q))
            else:
                self.assertEqual(result.grade, 0, "Test {} passed".format(q))

    def test_check_no_env(self):
        """
        Checks that the ``Notebook`` class works correctly, with no global env input
        """
        grader = Notebook(TEST_FILES_PATH + "tests")

        for q_path in glob(TEST_FILES_PATH + "tests/*.py"):
            q = os.path.split(q_path)[1][:-3]
            result = grader.check(q)  # global_env=global_env)
            if q != "q2":
                self.assertEqual(result.grade, 1, f"Test {q} expected to pass but failed:\n{result}")
            else:
                self.assertEqual(result.grade, 0, f"Test {q} expected to fail but passed:\n{result}")

<<<<<<< HEAD
=======
    def test_check_raise_exception(self):
        """
        Checks that the otter.Notebook class check method correctly raises Exceptions
        when things go wrong
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        global_env = 0
        for q_path in glob(TEST_FILES_PATH + "tests/*.py"):
            q = os.path.split(q_path)[1][:-3]
            self.assertRaises(AttributeError,
                              lambda: grader.check(q, global_env=global_env))

>>>>>>> df8bdbea5af4799f98e477ec7eb05182858aec85
    def test_check_all_repr(self):
        """
        Checks that the representation of results as strings is correct
        """
        grader = Notebook(TEST_FILES_PATH + "tests")

        output = str(grader.check_all())

        # checks each question substring
        output_lst = [
            'q1:\n\n    All tests passed!\n',
            'q2:\n\n    \n    0 of 1 tests passed\n',
            'q3:\n\n    All tests passed!\n',
            'q4:\n\n    All tests passed!\n',
            'q5:\n\n    All tests passed!\n'
        ]

        for result in output_lst:
            self.assertTrue(output.count(result) == 1)

    def test_to_pdf_with_nb_path(self):
        """
        Checks for existence of notebook PDF
        This test is the general use case WITH a specified notebook path
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.to_pdf(TEST_FILES_PATH + "test-nb.ipynb", filtering=False)

        self.assertTrue(os.path.isfile(TEST_FILES_PATH + "test-nb.pdf"))
        # cleanup
        os.remove(TEST_FILES_PATH + "test-nb.pdf")

    def test_to_pdf_without_nb_path_case1_pass(self):
        """
        Checks for the existence of notebook PDF
        This test is for the case where notebook path is not defined,
        but there exists a .otter file specifing the IPYNB notebook name
        """
        responses.add(responses.GET, 'http://some.url/auth/google',
                      json={'Key': '1234125'}, status=404)
        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.to_pdf(nb_path = None, filtering=False)
        self.assertTrue(os.path.exists("test-nb.pdf"))
        # cleanup
        os.remove("test-nb.pdf")

    def test_to_pdf_without_nb_path_case2_fail(self):
        """
        Checks for correct error scenario for to_pdf method
        This test is for when np_path is set to None and multiple
        IPYNB notebooks exist in the working directory.
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        self.assertRaises(AssertionError,
                          lambda: grader.to_pdf(nb_path=None, filtering=False))

    def test_to_pdf_without_nb_path_case2_pass(self):
        """
        Checks for correct scenario on to_pdf method
        This test is for when np_path is set to None and only 1
        IPYNB notebook exists in the working directory.
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.to_pdf(nb_path=None, filtering = False)

        self.assertTrue(os.path.exists("test-nb.pdf"))
        # cleanup
        os.remove("test-nb.pdf")

    def test_to_pdf_without_nb_path_case3(self):
        """
        Checks for correct error scenario for to_pdf method
        This test is for when nb_path is set to None, should raise ValueError
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        self.assertRaises(ValueError,
                          lambda: grader.to_pdf(nb_path=None, filtering=False))

    def test_export_without_nb_path_case2_pass(self):
        """
        Checks for correct error scenario for export method
        This test is for when nb_path is set to None and
        there is only 1 IPYNB notebook in working directory
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.export(nb_path=None, filtering=False)

        self.assertTrue(os.path.isfile("test-nb.pdf"))
        with self.unzip_to_temp("test-nb.zip") as unzipped_dir:
            # breakpoint()
            self.assertDirsEqual(
                unzipped_dir,
                TEST_FILES_PATH + "export-correct/test/test-notebook",
                ignore_ext=[".pdf", ""]  # second ignores .OTTER_LOG files
            )
        # cleanup
        os.remove("test-nb.pdf")
        os.remove("test-nb.zip")

    def test_export_without_nb_path_case2_fail(self):
        """
        Checks for correct error scenario for export method
        This test is for when nb_path is set to None and
        there are multiple IPYNB notebooks in working directory
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        self.assertRaises(AssertionError,
                          lambda: grader.export(nb_path=None, filtering=False))

    def test_export_without_nb_path_case3(self):
        """
        Checks for correct error scenario for export method
        This test is for when nb_path is set to None and
        there are no IPYNB notebooks in the working directory
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        self.assertRaises(ValueError,
                          lambda: grader.export(nb_path=None, filtering=False))

    def test_export_no_error(self):
        """
        Checks export contents for existence of PDF and equality of zip
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        grader.export(TEST_FILES_PATH + "test-nb.ipynb", filtering=False)

        self.assertTrue(os.path.isfile(TEST_FILES_PATH + "test-nb.pdf"))

        with self.unzip_to_temp(TEST_FILES_PATH + "test-nb.zip") as unzipped_dir:
            # breakpoint()
            self.assertDirsEqual(
                unzipped_dir,
                TEST_FILES_PATH + "export-correct",
<<<<<<< HEAD
                ignore_ext=[".pdf", ""] # second ignores .OTTER_LOG files
=======
                ignore_ext=[".pdf", ""]  # second ignores .OTTER_LOG files
>>>>>>> df8bdbea5af4799f98e477ec7eb05182858aec85
            )

        # cleanup
        os.remove(TEST_FILES_PATH + "test-nb.pdf")
        os.remove(TEST_FILES_PATH + "test-nb.zip")

    def test_export_multiple_otter_error(self):
        """
        Checks export for error scenario for export method
        This test should pass when export successfully raises an
        AssertionError for the case when the directory contains
        multiple .otter files.
        """
        grader = Notebook(TEST_FILES_PATH + "tests")
        self.assertRaises(AssertionError,
                          lambda: grader.export(nb_path=None, filtering=False))

    @patch.object(LogEntry, "shelve")
    def test_nb_log(self, mock_log):
        """
        Checks existence of log when running nb
        """

        mock_log.return_value = LogEntry(EventType.CHECK)
        grader = Notebook(TEST_FILES_PATH + "tests")
        output = grader.check_all()

        self.assertTrue(os.path.isfile(_OTTER_LOG_FILENAME))

    def tearDown(self):
        if os.path.isfile(_OTTER_LOG_FILENAME):
            os.remove(_OTTER_LOG_FILENAME)
