# Installation

Otter is a Python package that can be installed using pip:

```
pip install otter-grader
```

## Docker

Otter uses Docker to create containers in which to run the students' submissions. Please make sure that you install Docker and pull our Docker image, which is used to grade the notebooks.

### Pull from DockerHub

To pull the image from DockerHub, run `docker pull ucbdsinfra/otter-grader`. If you choose this method, otter will automatically use this image for you.

### Download the Dockerfile from GitHub

To install from the GitHub repo, follow the steps below:

1. Clone the GitHub repo
2. `cd` into the `otter-grader/docker` directory
3. Build the Docker image with this command: `docker build . -t YOUR_DESIRED_IMAGE_NAME`

_Note:_ With this setup, you will need to pass in a custom docker image name when using the CLI with the `--image` flag.
