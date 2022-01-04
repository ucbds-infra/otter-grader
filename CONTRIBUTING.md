# Contributing

This project welcomes contributions and suggestions. Please submit a PR to the `master` branch with 
any updates. Make sure to update the changelog with any information about the contribution.


## Environment Setup

To set up an environment for working on Otter, we recommend using 
[Conda](https://docs.conda.io/en/latest/miniconda.html). This repo contains an 
[`environment.yml`](environment.yml) file which defines all of the requirements for an environment
used to work on Otter.

Running

```
conda env create -f environment.yml
```

will create a conda environment called `otter-grader` with the necessary packages installed for both
Python and R.


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


### Test Docker Images

To build a Docker image suitable for testing, use the Makefile target `docker-test`. This will
build a Docker image tagged `otter-test` which includes the development version of Otter in your 
local copy of the repo as the installed version of Otter.

```
make docker-test
```

If you need to build testing images for grading assignments, use the `docker-grade-test` target to 
edit the Dockerfile in `otter/grade` and then install your local copy of the rpeo:

```
make docker-grade-test
pip install .
```

**Do not commit any changes made by this Makefile target.**

Once you finish, make sure to run the `cleanup-docker-grade-test` target to undo your changes. 

```
make cleanup-docker-grade-test
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
