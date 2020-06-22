# Otter-Grader

[![Build Status](https://travis-ci.org/ucbds-infra/otter-grader.svg?branch=master)](https://travis-ci.org/ucbds-infra/otter-grader)
[![codecov](https://codecov.io/gh/ucbds-infra/otter-grader/branch/master/graph/badge.svg)](https://codecov.io/gh/ucbds-infra/otter-grader)
[![Documentation Status](https://readthedocs.org/projects/otter-grader/badge/?version=latest)](https://otter-grader.readthedocs.io/en/latest/?badge=latest)
[![Custom badge](https://img.shields.io/endpoint?logo=slack&url=https%3A%2F%2Fraw.githubusercontent.com%2Fucbds-infra%2Fotter-grader%2Fmaster%2Fslack-shields.json)](https://join.slack.com/t/otter-grader/shared_invite/enQtOTM5MTQ0MzkwMTk0LTBiNWIzZTYxNDA2NDZmM2JkMzcwZjA4YWViNDM4ZTgyNDVhNDgwOTQ0NjNlZjcwNmY5YzJiZjZhZGNhNzc5MjA)

Otter-Grader is an open-source local grader from the Division of Computing, Data Science, and Society at the University of California, Berkeley. It is designed to be a scalable grader that utilizes parallel Docker containers on the instructor's machine in order to remove the traditional overhead requirement of a live server. It also supports student-run tests in Jupyter Notebooks and from the command line, and is compatible with Gradescope's proprietary autograding service.

## Documentation

The documentation for Otter can be found [here](https://otter-grader.rtfd.io).

## Contributing

PRs are welcome! Please submit a PR to the master branch with any updates. Make sure to update the changelog in the docs with any information about the contribution.

To set up the testing environment, install the requirements in `requirements.txt` and run the `test` directory as a module to execute the tests:

```
python3 -m test
```

To run the tests for a specific tool, add the command-line path for that tool to the command. For example, to run the tests for `otter generate autograder`, run

```
python3 -m test generate autograder
```

or to run all tests for commands under `otter generate`, run

```
python3 -m test generate
```

## Changelog

The changelog can be found in the [documentation](https://otter-grader.rtfd.io).
