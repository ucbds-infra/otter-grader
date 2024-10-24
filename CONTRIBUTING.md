# Contributing

This project welcomes contributions and suggestions. Please submit a PR to the `master` branch with 
any updates. Make sure to update the changelog with any information about the contribution.


## Environment Setup

To set up an environment for working on Otter, we recommend using [Mamba](https://mamba.readthedocs.io/en/latest/) (or Conda). This repo contains an 
[`environment.yml`](environment.yml) file which defines all of the requirements for an environment
used to work on Otter.

Running

```
mamba env create -f environment.yml
```

will create a conda environment called `otter-grader` with the necessary Python and R versions.

To install development dependencies, use [`poetry`](https://python-poetry.org/) to update the environment:

```
mamba activate otter-grader
poetry install --with dev,test
```


## Code Formatting

The Python files in this repo are formatted with isort and black. Installing the `dev` dependencies
with poetry will install these as well. You can run `make format` with your conda/virtual environment
activated to format the files in-place.

Note that code formatting is enforced by a CI test.


## Running Tests

To run the tests for Otter-Grader, use the `test` `Makefile` target:

```
make test
```

Tests that require Docker or which run slowly are marked as such. To disable these tests when running
the test suite, use `DOCKER=false` and `SLOW=false`, resp. Note that all Docker tests are also marked
as slow, so `SLOW=false` will also skip Docker tests.

```
make test DOCKER=false
make test SLOW=false
```

To run a specific test file or function, use the `TESTPATH` argument:

```
make test TESTPATH=test/test_assign.py
```

To run the coverage, use the `testcov` target.

```
make testcov
```


## Building the Documentation

To build a local copy of the documentation, use the `docs` target of the Makefile.

```
make docs
```

This will create HTML output in the `docs/_build/html` directory which you can view in your browser.

To rebuild the tutorial ZIP file, run

```
make tutorial
```
