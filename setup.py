import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

# get version
env = {}
with open("otter/version.py") as f:
	exec(f.read(), env)
version = env["__version__"]

# get requirements
with open("requirements.txt") as f:
	install_requires = f.readlines()

setuptools.setup(
	name = "otter-grader",
	version = version,
	author = "Christopher Pyles",
	author_email = "otter-grader@berkeley.edu",
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
	install_requires=install_requires,
	# scripts=["bin/otter"],
	entry_points = {
		"console_scripts": [
			"otter=otter.cli:cli", 
			"gmail_oauth2=otter.plugins.builtin.gmail_notifications.bin.gmail_oauth2:main",
		],
	},
	package_data={
		"otter.export.exporters": ["templates/*", "templates/*/*"],
		"otter.generate": ["templates/*", "templates/*/*"],
		"otter.grade": ["Dockerfile"],
	},
)
