import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name = "otter-grader",
	version = "0.4.5",
	author = "UC Berkeley Division of Data Science and Information",
	author_email = "cpyles@berkeley.edu",
	description = "Jupyter Notebook Autograder",
	long_description = long_description,
	long_description_content_type = "text/markdown",
	url = "https://github.com/ucbds-infra/otter-grader",
	license = "BSD-3-Clause",
	packages = setuptools.find_packages(),
	classifiers = [
		"Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
	],
	install_requires=[
		"nb2pdf",
		"tornado==5.1.1"
	],
	scripts=["bin/otter"]
)