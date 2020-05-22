###############################################
##### In-Notebook Checks for Otter-Grader #####
###############################################

import inspect
import requests
import json
import os
import zipfile
import pickle

from getpass import getpass
from glob import glob
from nb2pdf import convert
from IPython import get_ipython
from IPython.display import display, HTML, Javascript

from .execute import check
from .export import export_notebook

_API_KEY = None
_OTTER_STATE_FILENAME = ".OTTER_STATE"

class Notebook:
	"""Notebook class for in-notebook autograding
	
	Args:
		test_dir (str, optional): Path to tests directory

	"""

	def __init__(self, test_dir="./tests"): #, config_path="config.json", otter_service_enabled=False):
		global _API_KEY
		assert os.path.isdir(test_dir), "{} is not a directory".format(test_dir)
		
		self._path = test_dir
		self._service_enabled = False
		# self._otter_service = otter_service_enabled

		# if self._otter_service == True:
		
		# assume using otter service if there is a .otter file
		otter_configs = glob("*.otter")
		if otter_configs:
			# check that there is only 1 config
			assert len(otter_configs) == 1, "More than 1 otter config file found"

			# load in config file
			with open(otter_configs[0]) as f:
				self._config = json.load(f)

			self._service_enabled = "endpoint" in self._config
			self._pregraded_questions = self._config.get("pregraded_questions", [])

			if self._service_enabled:
				# check that config file has required info
				assert all([key in self._config for key in ["endpoint", "auth", "assignment_id", "class_id", "notebook"]]), "config file missing required information"

				self._google_auth_url = os.path.join(self._config["endpoint"], "auth/google")
				self._default_auth_url = os.path.join(self._config["endpoint"], "auth")
				self._submit_url = os.path.join(self._config["endpoint"], "submit")

				self._auth()

	# TODO: cut out personal auth?
	def _auth(self):
		global _API_KEY
		assert self._service_enabled, 'notebook not configured for otter service'
		assert self._config["auth"] in ["google", "default"], "invalid auth provider"

		if _API_KEY is not None:
			self._api_key = _API_KEY
			return

		# have users authenticate with OAuth
		if self._config["auth"] == "google":
				# send them to google login page
				display(HTML(f"""
				<p>Please <a href="{self._google_auth_url}" target="_blank">log in</a> to Otter Service 
				and enter your API key below.</p>
				"""))

				self._api_key = input()

		# else have them auth with default auth
		else:
			print("Please enter a username and password.")
			username = input("Username: ")
			password = getpass("Password: ")

			# in-notebook auth
			response = requests.get(url=self._default_auth_url, params={"username":username, "password":password})
			self._api_key = response.content.decode("utf-8")
			# print("Your API Key is {}\n".format())
			# print("Paste this in and hit enter")
			# self._api_key = input()
		
		# store API key so we don't re-auth every time
		_API_KEY = self._api_key


	def _dump_state(self, new_state):
		"""Pickles and dumps state"""
		if os.path.isfile(_OTTER_STATE_FILENAME):
			with open(_OTTER_STATE_FILENAME, "rb") as f:
				current_state = pickle.load(f)
		else:
			current_state = {}
		
		current_state.update(new_state)

		with open(_OTTER_STATE_FILENAME, "wb+") as f:
			pickle.dump(current_state, f)


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
		assert os.path.isfile(test_path), "Test {} does not exist".format(question)
		
		# pass the correct global environment
		if global_env is None:
			global_env = inspect.currentframe().f_back.f_globals

		# run the check
		result = check(test_path, global_env)

		if question in self._pregraded_questions:
			self._dump_state({question: result})

		return result


	# @staticmethod
	def to_pdf(self, nb_path=None, filtering=True, pagebreaks=True, display_link=True):
		"""Exports notebook to PDF

		FILTER_TYPE can be "html" or "tags" if filtering by HTML comments or cell tags,
		respectively. 
		
		Args:
			nb_path (str): Path to iPython notebook we want to export
			filtering (bool, optional): Set true if only exporting a subset of nb cells to PDF
			pagebreaks (bool, optional): If true, pagebreaks are included between questions
			display_link (bool, optional): Whether or not to display a download link
		
		"""
		if nb_path is None and self._service_enabled:
			nb_path = self._config["notebook"]

		elif nb_path is None and glob("*.ipynb"):
			notebooks = glob("*.ipynb")
			assert len(notebooks) == 1, "nb_path not specified and > 1 notebook in working directory"
			nb_path = notebooks[0]

		elif nb_path is None:
			raise ValueError("nb_path is None and no otter-service config is available")

		# convert(nb_path, filtering=filtering, filter_type=filter_type)
		export_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)

		if display_link:
			# create and display output HTML
			out_html = """
			<p>Your file has been exported. Download it by right-clicking 
			<a href="{}" target="_blank">here</a> and selecting <strong>Save Link As</strong>.
			""".format(nb_path[:-5] + "pdf")
			
			display(HTML(out_html))


	def export(self, nb_path=None, export_path=None, pdf=True, filtering=True, pagebreaks=True, files=[], display_link=True):
		"""Exports a submission to a zipfile

		Creates a submission zipfile from a notebook at NB_PATH, optionally including a PDF export
		of the notebook and any files in FILES.
		
		Args:
			nb_path (str): Path to iPython notebook we want to export
			export_path (str, optional): Path at which to write zipfile
			pdf (bool, optional): True if PDF should be included
			filtering (bool, optional): Set true if only exporting a subset of nb cells to PDF
			pagebreaks (bool, optional): If true, pagebreaks are included between questions
			files (list, optional): Other files to include in the zipfile
			display_link (bool, optional): Whether or not to display a download link
		
		"""		
		if nb_path is None and self._service_enabled:
			nb_path = self._config["notebook"]

		elif nb_path is None and glob("*.ipynb"):
			notebooks = glob("*.ipynb")
			assert len(notebooks) == 1, "nb_path not specified and > 1 notebook in working directory"
			nb_path = notebooks[0]

		elif nb_path is None:
			raise ValueError("nb_path is None and no otter-service config is available")

		if export_path is None:
			zip_path = ".".join(nb_path.split(".")[:-1]) + ".zip"
		else:
			zip_path = export_path

		zf = zipfile.ZipFile(zip_path, mode="w")
		zf.write(nb_path)

		if pdf:
			pdf_path = ".".join(nb_path.split(".")[:-1]) + ".pdf"
			# convert(nb_path, filtering=filtering, filter_type=filter_type)
			export_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)
			zf.write(pdf_path)

		if self._pregraded_questions:
			zf.write(_OTTER_STATE_FILENAME)

		for file in files:
			zf.write(file)

		zf.close()

		if display_link:
			# create and display output HTML
			out_html = """
			<p>Your file has been exported. Click <a href="{}" target="_blank">here</a> 
			to download the zip file.</p>
			""".format(zip_path)
			
			display(HTML(out_html))


	def check_all(self):
		"""
		Runs all tests on this notebook.
		"""
		# TODO: this should use functions in execute.py to run tests in-sequence so that variable
		# name collisions are accounted for
		tests = glob(os.path.join(self._path, "*.py"))
		global_env = inspect.currentframe().f_back.f_globals
		for file in sorted(tests):
			test_name = os.path.split(file)[1][:-3]
			check_html = self.check(test_name, global_env)._repr_html_()
			check_html = "<p><strong>{}</strong></p>".format(test_name) + check_html
			display(HTML(check_html))


	def submit(self):
		assert self._service_enabled, 'notebook not configured for otter service'
		
		if not hasattr(self, '_api_key'):
			self._auth()

		notebook_path = os.path.join(os.getcwd(), self._config["notebook"])

		assert os.path.exists(notebook_path) and os.path.isfile(notebook_path), \
    	"Could not find notebook: {}".format(self._config["notebook"])

		with open(notebook_path) as f:
			notebook_data = json.load(f)

		notebook_data["metadata"]["assignment_id"] = self._config["assignment_id"]
		notebook_data["metadata"]["class_id"] = self._config["class_id"]
		
		print("Submitting notebook to server...")

		response = requests.post(self._submit_url, json.dumps({
			"api_key": self._api_key,
			"nb": notebook_data,
		}))

		print(response.text)
