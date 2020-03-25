########################################################
##### Command Line Script Checker for Otter-Grader #####
########################################################

# from .utils import remove_html_in_hint
from .execute import grade_notebook
from .gofer import check
from .utils import block_print, enable_print
import argparse
import os
from glob import glob
from jinja2 import Template
import re
import sys

RESULT_TEMPLATE = Template("""{% if grade == 1.0 %}All tests passed!{% else %}{{ passed_tests|length }} of {{ scores|length - 2 }} tests passed
{% if passed_tests %}
Tests passed:
{% for passed_test in passed_tests %} {{ passed_test }} {% endfor %}
{% endif %}
{% if failed_tests %}
Tests failed: 
{% for failed_test in failed_tests %}{{ failed_test }}{% endfor %}{% endif %}{% endif %}
""")

def main(args):

	if args.question:
		test_path = os.path.join(args.tests_path, args.question + ".py")
		assert os.path.isfile(test_path), "Test {} does not exist".format(args.question)
		qs = [test_path]
	else:
		qs = glob(os.path.join(args.tests_path, "*.py"))

	block_print()
	results = grade_notebook(
		args.file,
		tests_glob=qs,
		script=True
	)
	enable_print()

	# for q in results:
	# 	if "hint" in q:
	# 		results[q]["hint"] = remove_html_in_hint(results[q]["hint"])

	# print(results)

	passed_tests = [test for test in results if test not in ["possible", "total"] and "hint" not in results[test]]
	failed_tests = [results[test]["hint"] for test in results if test not in ["possible", "total"] and "hint" in results[test]]

	output = RESULT_TEMPLATE.render(
		grade=results["total"] / results["possible"],
		passed_tests=passed_tests,
		failed_tests=failed_tests,
		scores=results
	)

	print(output)

if __name__ == "__main__":
	main()
