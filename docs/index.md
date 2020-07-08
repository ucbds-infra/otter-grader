# Otter-Grader Documentation

```eval_rst
.. toctree::
   :maxdepth: 1
   :caption: Contents:
   :hidden:

   tutorial
   test_files
   otter_assign
   otter_check
   otter_grade
   otter_generate
   otter_service
   pdfs
   seeding
   logging
   changelog
```

Otter-Grader is an open-source local grader from the Division of Computing, Data Science, and Society at the University of California, Berkeley. It is designed to be a scalable grader that utilizes parallel Docker containers on the instructor's machine in order to remove the traditional overhead requirement of a live server. It also supports student-run tests in Jupyter Notebooks and from the command line, and is compatible with Gradescope's proprietary autograding service.

Otter is a command-line tool organized into six basic commands: `assign`, `check`, `export`, `generate`, `grade`, and `service`. These commands provide functionality that allows instructors to create, distribute, and grade assignments locally or using a variety of learning management system (LMS) integrations. Otter also allows students to run publically distributed tests while working through assignments.

* [Otter Assign](otter_assign.md) is an assignment development and distribution tool that allows instructors to create assignments with prompts, solutions, and tests in a simple notebook format that it then converts into santized versions for distribution to students and autograders.
* [Otter Check and the `otter.Notebook` class](otter_check.md) allow students to run publically distributed tests written by instructors against their solutions as they work through assignments to verify their thought processes and design implementations.
* [Otter Export](pdfs.md) generates PDFs with optional filtering of Jupyter Notebooks for manually grading portions of assignments.
* [Otter Generate](otter_generate.md) creates the necessary files so that instructors can autograde assignments using Gradescope's autograding platform.
* [Otter Grade](otter_grade.md) grades students' assignments locally on the instructor's machine in parallel Docker containers, returning grade breakdowns as a CSV file. It also supports [PDF generation an cell filtering with nb2pdf](pdfs.md) so that instructors can manually grade written portions of assignments.
* [Otter Service](otter_service.md) is a deployable grading server that students can submit their work to which grades these submissions and can optionally upload PDFs of these submission to Gradescope for manual grading.

## Installation

Otter is a Python package that can be installed using pip. To install the current stable version, install with

```
pip install otter-grader
```

To install the **beta** version, you must specify a semantic version, as pip won't install pre-release versions by default:

```
pip install otter-grader==1.0.0.b1
```

### Docker

Otter uses Docker to create containers in which to run the students' submissions. Please make sure that you install Docker and pull our Docker image, which is used to grade the notebooks.

#### Pull from DockerHub

To pull the image from DockerHub, run `docker pull ucbdsinfra/otter-grader`. If you choose this method, otter will automatically use this image for you.

#### Download the Dockerfile from GitHub

To install from the GitHub repo, follow the steps below:

1. Clone the GitHub repo
2. `cd` into the `otter-grader/docker` directory
3. Build the Docker image with this command: `docker build . -t YOUR_DESIRED_IMAGE_NAME`

_Note:_ With this setup, you will need to pass in a custom docker image name when using the CLI with the `--image` flag.
