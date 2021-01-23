import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

# get version
env = {}
with open("otter/version.py") as f:
	exec(f.read(), env)
version = env["__version__"]

setuptools.setup(
	name = "otter-grader",
	version = version,
	author = "Chris Pyles",
	author_email = "cpyles@berkeley.edu",
	description = "Python and Jupyter Notebook autograder",
	long_description = long_description,
	long_description_content_type = "text/markdown",
	url = "https://github.com/ucbds-infra/otter-grader",
	license = "BSD-3-Clause",
	packages = setuptools.find_packages(exclude=["test"]),
	classifiers = [
		"Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
	],
	install_requires=[
		"pyyaml", "nbformat", "ipython", "nbconvert", "tqdm", "setuptools", "pandas", "tornado",
		"docker", "jinja2", "dill", "pdfkit", "PyPDF2", "gspread"
	],
	# scripts=["bin/otter"],
	entry_points = {
		"console_scripts": ["otter=otter.runner:run_otter"]
	},
	package_data={
		"otter.service": ["templates/*.html"],
		"otter.export.exporters": ["templates/*", "templates/*/*"],
		"otter.generate": ["templates/*", "templates/*/*"],
		"otter.grade": ["Dockerfile"],
	},
)
