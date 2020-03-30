###############################################
##### In-Notebook Checks for Otter-Grader #####
###############################################

import inspect
import requests
import json
import os

from getpass import getpass
from glob import glob
from nb2pdf import convert
from IPython.display import display, HTML

from .execute import check

class Notebook:
	"""Notebook class for in-notebook autograding
	
	Args:
		test_dir (str, optional): Path to tests directory

	"""

	def __init__(self, test_dir="./tests"):#, config_path="config.json", otter_service_enabled=False):
		self._path = test_dir
		# self._otter_service = otter_service_enabled

		# if self._otter_service == True:
		
		# assume using otter service if there is a .otter file
		if glob("*.otter"):
			# check that config_path exists
			assert os.path.exists(config_path) and os.path.isfile(config_path), \
			"{} is not a valid config path".format(config_path)

			# load in config file
			with open(config_path) as f:
				self._config = json.load(f)

			# check that config file has required info
			assert all([i in self._config for i in ["server_url", "auth", "notebook"]]), \
			"config file missing required information"
			assert self._config["auth"] in ["google", "none"], "invalid auth provider"

			self._google_auth_url = os.path.join(self._config["server_url"], "google_auth")
			self._submit_url = os.path.join(self._config["server_url"], "submit")

	def check(self, question, global_env=None):
		"""Checks question using gofer
		
		Args:
			question (str): Name of question being graded
			global_env (dict): Global environment resulting from execution of a single 
				notebook/script (see execute.execute_notebook for more on this)

		Returns:
			OKTestsResult: Result of running gofer.check which contains grade, failed tests, and
				more related information (see gofer.OKTestsResult for more)

		"""
		test_path = os.path.join(self._path, question + ".py")

		# ensure that desired test exists
		assert os.path.exists(test_path) and \
			os.path.isfile(test_path), "Test {} does not exist".format(question)
		
		# pass the correct global environment
		if global_env is None:
			global_env = inspect.currentframe().f_back.f_globals

		# pass the check to gofer
		return check(test_path, global_env)

	@staticmethod
	def export(nb_path, filtering=True, filter_type="html"):
		"""Exports notebook to PDF

		FILTER_TYPE can be "html" or "tags" if filtering by HTML comments or cell tags,
		respectively. 
		
		Args:
			nb_path (str): Path to iPython notebook we want to export
			filtering (bool, optional): Set true if only exporting a subset of nb cells to PDF
			filter_type (str, optional): "html" or "tags" if filtering by HTML comments or cell
				tags, respectively.
		
		"""
		convert(nb_path, filtering=filtering, filter_type=filter_type)

		# create and display output HTML
		out_html = """
		<p>Your file has been exported. Download it 
		<a href="{}" target="_blank">here</a>!
		""".format(nb_path[:-5] + "pdf")
		
		display(HTML(out_html))

	def check_all(self):
		"""
		Runs all tests on this notebook.
		"""
		tests = glob(os.path.join(self._path, "*.py"))
		global_env = inspect.currentframe().f_back.f_globals
		for file in sorted(tests):
			test_name = os.path.split(file)[1][:-3]
			check_html = self.check(test_name, global_env)._repr_html_()
			check_html = "<p><strong>{}</strong></p>".format(test_name) + check_html
			display(HTML(check_html))
	
	def _auth(self):
		assert self._otter_service == True, 'notebook not configured for otter service'

		# have users authenticate with OAuth
		if "auth" in self._config and self._config["auth"] != "default":
			if self._config["auth"] == "google":
				# send them to google login page
				display(HTML(f"""
				<p>Please <a href="{self._google_auth_url}" target="_blank">log in</a> to the 
				otter grader server and enter your API key below.</p>
				"""))

				self._api_key = input()

		# else have them auth with default auth
		else:
			print("Please enter a username and password.")
			username = input("Username: ")
			password = getpass("Password: ")

			#in-notebook auth
			response = requests.get(url=os.path.join(self._config["server_url"], "personal_auth"), params={"username":username, "password":password})
			print("Your API Key is {}\n".format(response.content.decode("utf-8")))
			print("Paste this in and hit enter")
			self._api_key = input()

	def _submit(self):
		assert self._otter_service == True, 'notebook not configured for otter service'
		
		if not hasattr(self, '_api_key'):
			self._auth()

		notebook_path = os.path.join(os.getcwd(), self._config["notebook"])
		assert os.path.exists(notebook_path) and os.path.isfile(notebook_path), \
    "Could not find notebook: {}".format(self._config["notebook"])

		with open(notebook_path) as f:
			notebook_data = json.load(f)
		print("Submitting notebook to server")
		response = requests.post(self._submit_url, json.dumps({
			"api_key": self._api_key,
			"nb": notebook_data,
		}))

		print(response.text)
