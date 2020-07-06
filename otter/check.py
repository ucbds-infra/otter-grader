########################################################
##### Command Line Script Checker for Otter-Grader #####
########################################################

import os

from glob import glob
from jinja2 import Template

from .execute import grade_notebook, check
from .logs import LogEntry, EventType
from .notebook import _OTTER_LOG_FILENAME
from .utils import block_print


RESULT_TEMPLATE = Template("""{% if grade == 1.0 %}All tests passed!{% else %}{{ passed_tests|length }} of {{ tests|length }} tests passed
{% if passed_tests %}
Tests passed:
    {% for passed_test in passed_tests %}{{ passed_test }} {% endfor %}
{% endif %}
{% if failed_tests %}
Tests failed: 
{% for failed_test in failed_tests %}{{ failed_test }}{% endfor %}{% endif %}{% endif %}
""")

def _log_event(event_type, results=[], question=None, success=True, error=None):
	"""Logs an event

	Args:
		event_type (``otter.logs.EventType``): the type of event
		results (``list`` of ``otter.ok_parser.OKTestsResult``, optional): the results of any checks
			recorded by the entry
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

def main(args):
	"""Runs Otter Check

	Args:
		args (``argparse.Namespace``): parsed command line arguments
	"""

	try:
		if args.question:
			test_path = os.path.join(args.tests_path, args.question + ".py")
			assert os.path.isfile(test_path), "Test {} does not exist".format(args.question)
			qs = [test_path]
		else:
			qs = glob(os.path.join(args.tests_path, "*.py"))

		assert os.path.isfile(args.file), "{} is not a file".format(args.file)
		assert args.file[-6:] == ".ipynb" or args.file[-3:] == ".py", "{} is not a Jupyter Notebook or Python file".format(args.file)

		script = args.file[-3:] == ".py"

		with block_print():
			results = grade_notebook(
				args.file,
				tests_glob=qs,
				script=script,
				seed=args.seed
			)

		passed_tests = [
			results.get_result(test_name).name for test_name in results.tests if not results.get_result(test_name).incorrect
			# test for test in results if test not in ["possible", "total"] and "hint" not in results[test]
		]
		failed_tests = [
			repr(results.get_result(test_name).test) for test_name in results.tests if results.get_result(test_name).incorrect
		]

		output = RESULT_TEMPLATE.render(
			grade=results.total / results.possible,
			passed_tests=passed_tests,
			failed_tests=failed_tests,
			tests=results.tests
		)

		print(output)

	except Exception as e:
		_log_event(EventType.CHECK, success=False, error=e)
			
	else:
		_log_event(EventType.CHECK, results=results)
