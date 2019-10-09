###############################################
##### In-Notebook Checks for Otter-Grader #####
###############################################

from gofer.ok import check
import inspect
import os

class Notebook:
	"""Notebook class for in-notebook autograding"""

	def __init__(self, test_dir="./tests"):
		self._path = test_dir

	def check(self, question, global_env=None):
		test_path = os.path.join(self._path, question + ".py")

		# ensure that desired test exists
		assert os.path.exists(test_path) and \
			os.path.isfile(test_path), "Test {} does not exist".format(question)
		
		# pass the correct global environment
		if global_env is None:
			global_env = inspect.currentframe().f_back.f_globals

		# pass the check to gofer
		return check(test_path, global_env)