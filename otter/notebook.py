###############################################
##### In-Notebook Checks for Otter-Grader #####
###############################################

from .gofer import check
import inspect
import os
from nb2pdf import convert
from IPython.display import display, HTML
from glob import glob

class Notebook:
	"""Notebook class for in-notebook autograding
	
	Args:
		test_dir (str, optional): Path to tests directory

	"""

	def __init__(self, test_dir="./tests"):
		self._path = test_dir

	def check(self, question, global_env=None):
		"""Checks question using gofer
		
		Args:
			question (str): Name of question being graded
			global_env (dict): Global environment resulting from execution of a single 
				notebook/script (see grade.execute_notebook for more on this)

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
