########################################################
##### Command Line Script Checker for Otter-Grader #####
########################################################

import os

from glob import glob
from jinja2 import Template

from .execute import grade_notebook, check
from .utils import block_print, enable_print


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

	assert os.path.isfile(args.file), "{} is not a file".format(args.file)
	assert args.file[-6:] == ".ipynb" or args.file[-3:] == ".py", "{} is not a Jupyter Notebook or Python file".format(args.file)

	block_print()
	results = grade_notebook(
		args.file,
		tests_glob=qs,
		script=args.file[-3:] == ".py",
		seed=args.seed
	)
	enable_print()

	passed_tests = [test for test in results if test not in ["possible", "total"] and "hint" not in results[test]]
	failed_tests = [results[test]["hint"] for test in results if test not in ["possible", "total"] and "hint" in results[test]]

	output = RESULT_TEMPLATE.render(
		grade=results["total"] / results["possible"],
		passed_tests=passed_tests,
		failed_tests=failed_tests,
		scores=results
	)

	print(output)
