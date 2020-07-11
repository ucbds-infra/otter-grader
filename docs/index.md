# Otter-Grader Documentation -- Beta Version

```eval_rst
.. toctree::
   :maxdepth: 1
   :caption: Contents:
   :hidden:

   tutorial
   test_files
   otter_assign
   otter_check
   dot_otter_files
   otter_grade
   otter_generate
   otter_service
   pdfs
   seeding
   logging
   changelog
```

**This is the documentation for the current beta version of Otter Grader. For the last stable release, visit [https://otter-grader.readthedocs.io/en/stable/](https://otter-grader.readthedocs.io/en/stable/).**

Otter Grader is a light-weight, modular open-source autograder developed by the Data Science Education Program at UC Berkeley. It is designed to work with classes at any scale by abstracting away the autograding internals in a way that is compatible with any instructor's assignment distribution and collection pipeline. Otter supports local grading through parallel Docker containers, grading using the autograder platforms of 3rd party learning management systems (LMSs), the deployment of an Otter-managed grading virtual machine, and a client package that allows students to run public checks on their own machines. Otter is designed to grade Python scripts and Jupyter Notebooks, and is compatible with a few different LMSs, including Canvas and Gradescope.

Otter is managed by a command-line tool organized into six basic commands: `assign`, `check`, `export`, `generate`, `grade`, and `service`. These commands provide functionality that allows instructors to create, distribute, and grade assignments locally or using a variety of learning management system (LMS) integrations. Otter also allows students to run publically distributed tests while working through assignments.

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
pip install git+https://github.com/ucbds-infra/otter-grader.git@aa012b79a296d3a790a9b6f1d70c519f850ea2bb
```

### Docker

Otter uses Docker to create containers in which to run the students' submissions. Please make sure that you install Docker and pull our Docker image, which is used to grade the notebooks. We have the current beta version of Otter installed on the `beta` release of the image. To get the Docker image, run

```
docker pull ucbdsinfra/otter-grader:beta
```
