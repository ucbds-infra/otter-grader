# Otter-Grader

[![Build Status](https://travis-ci.org/ucbds-infra/otter-grader.svg?branch=master)](https://travis-ci.org/ucbds-infra/otter-grader)
[![codecov](https://codecov.io/gh/ucbds-infra/otter-grader/branch/master/graph/badge.svg)](https://codecov.io/gh/ucbds-infra/otter-grader)
[![Documentation Status](https://readthedocs.org/projects/otter-grader/badge/?version=latest)](https://otter-grader.readthedocs.io/en/latest/?badge=latest)
[![Custom badge](https://img.shields.io/endpoint?logo=slack&url=https%3A%2F%2Fraw.githubusercontent.com%2Fucbds-infra%2Fotter-grader%2Fmaster%2Fslack-shields.json)](https://join.slack.com/t/otter-grader/shared_invite/enQtOTM5MTQ0MzkwMTk0LTBiNWIzZTYxNDA2NDZmM2JkMzcwZjA4YWViNDM4ZTgyNDVhNDgwOTQ0NjNlZjcwNmY5YzJiZjZhZGNhNzc5MjA)

Otter-grader is a new, open-source, local grader from the Division of Data Science, External Pedagogy Infrastructure at UC Berkeley. It is designed to be a scalable grader that utilizes temporal docker containers in order to remove the traditional overhead requirement of a live server. 

## Documentation

The documentation for Otter can be found [here](https://otter-grader.rtfd.io).

## Changelog

**v0.4.7:**

* fix relative import issue on Gradescope (again, *sigh*)

**v0.4.6:** re-release of v0.4.5

**v0.4.5:**

* added missing patch of `otter.Notebook.export` in [otter/grade.py](otter/grade.py)
* added `__version__` global in [otter/__init__.py](otter/__init__.py)
* fixed relative import issue when running on Gradescope
* fixed not finding/rerunning tests on Gradescope with `otter.Notebook.check`

**v0.4.4:**

* fixed template escape bug in [otter/gs_generator.py](otter/gs_generator.py)

**v0.4.3:**

* fixed dead link in [docs/gradescope.md](docs/gradescope.md)
* updated to Python 3.7 in setup.sh for Gradescope
* made `otter` and `otter gen` CLIs find `./requirements.txt` automatically if it exists
* fix bug where GS generator fails if no `-r` flag specified
