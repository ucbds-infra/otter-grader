########################################################
##### Command Line Script Checker for Otter-Grader #####
########################################################

# from .utils import remove_html_in_hint
from .grade import grade_notebook
from .gofer import check
import argparse
import os
from glob import glob
from jinja2 import Template
import re
import sys

# Disable
def blockPrint():
	"""
	Disables printing to stdout.
	"""
	sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
	"""
	Enables printing to stdout.
	"""
	sys.stdout = sys.__stdout__

RESULT_TEMPLATE = Template("""{% if grade == 1.0 %}All tests passed!{% else %}{{ passed_tests|length }} of {{ scores|length - 2 }} tests passed
{% if passed_tests %}
Tests passed:
{% for passed_test in passed_tests %} {{ passed_test }} {% endfor %}
{% endif %}
{% if failed_tests %}
Tests failed: 
{% for failed_test in failed_tests %}{{ failed_test }}{% endfor %}{% endif %}{% endif %}
""")

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("file", help="Python file to grade")
	parser.add_argument("-q", dest="question", help="Grade a specific test")
	parser.add_argument("-t", dest="tests-path", default="tests", help="Path to test files")
	params = vars(parser.parse_args())

	if params["question"]:
		test_path = os.path.join(params["tests-path"], params["question"] + ".py")
		assert os.path.exists(test_path) and \
			os.path.isfile(test_path), "Test {} does not exist".format(params["question"])
		qs = [test_path]
	else:
		qs = glob(os.path.join(params["tests-path"], "*.py"))

	blockPrint()
	results = grade_notebook(
		params["file"],
		tests_glob=qs,
		script=True
	)
	enablePrint()

	for q in results:
		if "hint" in q:
			results[q]["hint"] = remove_html_in_hint(results[q]["hint"])

	passed_tests = [test for test in results if test not in ["possible", "total"] and results[test] == 1 and "hint" not in results[test]]
	failed_tests = [results[test]["hint"] for test in results if test not in ["possible", "total"] and "hint" in results[test]]

	output = RESULT_TEMPLATE.render(
		grade=results["total"],
		passed_tests=passed_tests,
		failed_tests=failed_tests,
		scores=results
	)

	print(output)

if __name__ == "__main__":
	main()
