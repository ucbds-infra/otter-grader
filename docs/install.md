# Installation


```
pip install otter-grader
```

## Docker

Otter also requires you to have its Docker image installed, which is where it executes notebooks. The docker image can be installed in two ways:

### Pull from DockerHub

To pull the image from DockerHub, run `docker pull ucbdsinfra/otter-grader`.

### Download the Dockerfile from GitHub

To install from the GitHub repo, follow the steps below:

1. Clone the GitHub repo
2. `cd` into the `otter-grader/docker` directory
3. Build the Docker image with this command: `docker build . -t YOUR_DESIRED_IMAGE_NAME`

_Note:_ With this setup, you will need to pass in a custom docker image name when using the CLI with the `--image` flag.
