# Otter-Grader Documentation

```eval_rst
.. toctree::
   :maxdepth: 1
   :hidden:

   tutorial
   test_files/index
   otter_assign/index
   workflow/index
   otter_check/index
   execution
   plugins/index
   pdfs
   seeding
   logging
   api_reference
   cli_reference
   resources
   changelog
```

**This is the documentation for the development version of Otter Grader. For the last stable release, visit [https://otter-grader.readthedocs.io/en/stable/](https://otter-grader.readthedocs.io/en/stable/).**

<!-- TODO: rewrite this -->

Otter Grader is a light-weight, modular open-source autograder developed by the Data Science Education Program at UC Berkeley. It is designed to grade Python and R assignments for classes at any scale by abstracting away the autograding internals in a way that is compatible with any instructor's assignment distribution and collection pipeline. Otter supports local grading through parallel Docker containers, grading using the autograding platforms of 3rd-party learning management systems (LMSs), the deployment of an Otter-managed grading virtual machine, and a client package that allows students to check and instructors to grade assignments their own machines. Otter is designed to grade Pyhon and R executabeles, Jupyter Notebooks, and RMarkdown documents and is compatible with a few different LMSs, including Canvas and Gradescope.

Otter is organized into seven components based on the different stages of the assignment pipeline, each with a command-line interface:

* [Otter Assign](otter_assign/index.md) is an assignment development and distribution tool that allows instructors to create assignments with prompts, solutions, and tests in a simple notebook format that it then converts into santized versions for distribution to students and autograders.
* [Otter Generate](workflow/otter_generate/index.md) creates the necessary setup files so that instructors can autograde assignments.
* [Otter Check](otter_check/index.md) allows students to run publically distributed tests written by instructors against their solutions as they work through assignments to verify their thought processes and design implementations.
* [Otter Export](pdfs.md) generates PDFs with optional filtering of Jupyter Notebooks for manually grading portions of assignments.
* [Otter Run](workflow/executing_submissions/otter_run.md) grades students' assignments locally on the instructor's machine without containerization and supports grading on a JupyterHub account.
* [Otter Grade](workflow/executing_submissions/otter_grade.md) grades students' assignments locally on the instructor's machine in parallel Docker containers, returning grade breakdowns as a CSV file.
* [Otter Service](otter_service.md) is a deployable grading server that students can submit their work to which grades these submissions and can optionally upload PDFs of these submission to Gradescope for manual grading.

## Installation

Otter is a Python package that is compatible with Python 3.6+. The PDF export internals require either LaTeX and Pandoc or wkhtmltopdf to be installed. Docker is also required to grade assignments locally with containerization, and Postgres only if you're using Otter Service. Otter's Python package can be installed using pip. To install the current stable version, install with

```
pip install otter-grader
```

If you are going to be autograding R, you must also install the R package using `devtools::install_github`:

```r
devtools::install_github("ucbds-infra/ottr@stable")
```

Installing the Python package will install the `otter` binary so that Otter can be called from the command line. **If you are running Otter on Windows,** this binary will not work. Instead, call Otter as a Python module: `python3 -m otter`. This will have _the same_ commands, arguments, and behaviors as all calls to `otter` that are shown in the documentation. 

### Docker

Otter uses Docker to create containers in which to run the students' submissions. **Docker and our Docker image are only required if using Otter Grade or Otter Service.** Please make sure that you install Docker and pull our Docker image, which is used to grade the notebooks. To get the Docker image, run

```
docker pull ucbdsinfra/otter-grader
```
