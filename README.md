# Otter-Grader

[![Build Status](https://travis-ci.org/ucbds-infra/otter-grader.svg?branch=master)](https://travis-ci.org/ucbds-infra/otter-grader)
[![codecov](https://codecov.io/gh/ucbds-infra/otter-grader/branch/master/graph/badge.svg)](https://codecov.io/gh/ucbds-infra/otter-grader)
[![Demo](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ucbds-infra/otter-grader/master?filepath=demo%2Fdemo.ipynb)

Otter-grader is a new, open-source, local grader from the Division of Data Science, External Pedagogy Infrastructure at UC Berkeley. It is designed to be a scalable grader that utilizes temporal docker containers in order to remove the traditional overhead requirement of a live server. 

## Installation

Otter-grader can be installed using pip:

```
pip install otter-grader
```

### Docker

Otter also requires you to have its Docker image installed, which is where it executes notebooks. The docker image can be installed in two ways:

#### Pull from DockerHub

To pull the image from DockerHub, run `docker pull ucbdsinfra/otter-grader`.

#### Download the Dockerfile from GitHub

To install from the GitHub repo, follow the steps below:

1. Clone the GitHub repo
2. `cd` into the `otter-grader/docker` directory
3. Build the Docker image with this command: `docker build . -t YOUR_DESIRED_IMAGE_NAME`

_Note:_ With this setup, you will need to pass in a custom docker image name when using the CLI.

## Documentation

You can find the documentation in the demo notebook by clicking the Binder link above, or by viewing the static HTML version [here](https://nbviewer.jupyter.org/github/ucbds-infra/otter-grader/blob/master/demo/demo.ipynb).
