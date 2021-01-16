"""
Otter Check command-line utility
"""

import os

from glob import glob
from jinja2 import Template

from .logs import LogEntry, EventType
from .notebook import _OTTER_LOG_FILENAME
from ..execute import grade_notebook, check
from ..utils import block_print


def _log_event(event_type, results=[], question=None, success=True, error=None):
	"""
	Logs an event

	Args:
		event_type (``otter.logs.EventType``): the type of event
		results (``list`` of ``otter.test_files.abstract_test.TestCollectionResults``, optional): the 
			results of any checks recorded by the entry
		question (``str``, optional): the question name for this check
		success (``bool``, optional): whether the operation was successful
		error (``Exception``, optional): the exception thrown by the operation, if applicable
	"""
	LogEntry(
		event_type,
		results=results,
		question=question, 
		success=success, 
		error=error
	).flush_to_file(_OTTER_LOG_FILENAME)

def main(file, tests_path, question, seed, **kwargs):
	"""
	Runs Otter Check

	Args:
		file (``str``): path to the file to check
		tests_path (``str``): path to tests directory
		question (``str``): test name to run; ``None`` if all tests should be run
		seed (``int``): a seed to set before execution
		**kwargs: ignored kwargs (a remnant of how the argument parser is built)
	"""

	try:
		if question:
			test_path = os.path.join(tests_path, question + ".py")
			assert os.path.isfile(test_path), "Test {} does not exist".format(question)
			qs = [test_path]
		else:
			qs = glob(os.path.join(tests_path, "*.py"))

		assert os.path.isfile(file), "{} is not a file".format(file)
		assert file[-6:] == ".ipynb" or file[-3:] == ".py", "{} is not a Jupyter Notebook or Python file".format(file)

		script = file[-3:] == ".py"

		with block_print():
			results = grade_notebook(
				file,
				tests_glob=qs,
				script=script,
				seed=seed
			)

		if results.total / results.possible == 1:
			output = "All tests passed!"
		else:
			output = "\n".join(repr(test_file) for test_file in results.test_files)

		print(output)

	except Exception as e:
		_log_event(EventType.CHECK, success=False, error=e)
		raise e
			
	else:
		_log_event(EventType.CHECK, results=results)
