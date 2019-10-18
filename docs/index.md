# Otter-Grader Onboarding Guide

Otter-grader is a new, open-source, local grader from the Division of Data Science, External Pedagogy Infrastructure at UC Berkeley. It is designed to be a scalable grader that utilizes temporal docker containers in order to remove the traditional overhead requirement of a live server. 

## Installation

Otter-grader can be installed using pip:

```
pip install otter-grader
```

### Docker

#### Pull from Dockerhub

To pull the image from Dockerhub, run `docker pull ucbdsinfra/otter-grader`.

#### Download the Dockerfile from Github

To install from the Github repo, follow the steps below:

1. Clone the Github repo
2. `cd` into the `otter-grader/docker` directory
3. Build the Docker image with this command: `docker build . -t otter-grader`

## Usage

### Notebook Design

Otter-grader uses nb2pdf to generate manual submissions as PDFs. When generating the PDF, the following cells will be included by default:

* Markdown cells
* Code cells with images in the output
* All cells tagged with `include`

If a cell falls within one of the 3 categories listed above but you do not want to include it in the exported PDF, tag the cell with `ignore`. This cell will then not be added to the manual graded PDF.

### Ok-Formatted Tests

You can use [https://oktests.herokuapp.com/](https://oktests.herokuapp.com/) to generate your tests in the okpy format. Place all generated test files in the tests directory. 

### In-Notebook Usage

#### Instantiating the Autograder

Otter has functionality to allow it to be used in Jupyter Notebooks to allow students to check their progress against tests distributed with the notebook. This functionality is encapsulated in the `otter.Notebook` class which allows you to run tests as you go through the notebook. When this class is initialized, it automatically assumes that the tests are located in the `tests` subdirectory of the directory that contains the notebook, e.g.

```
lab01
| - lab01.ipynb
| tests
  | - q1.py
  | - q2.py
  ...
```

To initialize the class, simply import it and create an instance:

```python
import otter
grader = otter.Notebook()
```

To use a custom directory of tests, pass it as the argument to the `Notebook` constructor:

```python
import otter
grader = otter.Notebook("/path/to/your/tests")
```

#### Checking Questions and Exporting

To run a test case, use the `Notebook.check` function, which takes the test name as its argument. For example, if I wanted to run the test located in `tests/q1_1.py`, I would call

```
grader.check("q1_1")
```

Note the lack of the `.py` extension; `Notebook.check` automatically adds this when finding the test case.

Although it is possible to export manual submission PDFs from the command line usage of otter, the `Notebook` API includes a method that exports the notebook for each student so that they can submit these themselves. This functionality is included because generating all PDFs at once requires a significant amount of time. To have students export their own notebooks, add the cell below to the notebook.

```python
grader.export("/path/to/notebook")
```

For example, if I was working in a notebook called `lab01.ipynb`, my call to `Notebook.export` would be

```python
grader.export("lab01.ipynb")
```

### Command Line Usage

The help entry for the `otter` command is given below.

```
usage: otter [-h] [-g] [-c] [-j JSON] [-y YAML] [-n NOTEBOOKS-PATH]
             [-t TESTS-PATH] [-o OUTPUT-PATH] [-v] [-r REQUIREMENTS] [--pdf]

optional arguments:
  -h, --help            show this help message and exit
  -g, --gradescope
  -c, --canvas
  -j JSON, --json JSON
  -y YAML, --yaml YAML
  -n NOTEBOOKS-PATH, --notebooks-path NOTEBOOKS-PATH
  -t TESTS-PATH, --tests-path TESTS-PATH
  -o OUTPUT-PATH, --output-path OUTPUT-PATH
  -v, --verbose
  -r REQUIREMENTS, --requirements REQUIREMENTS
  --pdf
```

Using otter requires a metadata file, which can be set for Gradescope (`-g`) or Canvas (`-c`) exports, JSON format (`-j`), or YAML format (`-y`). The JSON and YAML flags require an argument corresponding to the name of the metadata file _relative to the `--notebooks-path` argument_. Note that you can only specify ONE (1) of the metadata flags. The defaults for certain flags are given below.

| Flag | Default Value |
|------|---------------|
| `-n` | `./`, the current working directory |
| `-t` | `./tests`, the `tests` subdirectory of the current working directory |
| `-o` | `./`, the current working directory |

An example command would be

```
otter -g -n ./notebooks -t ./tests -o ./outputs -v
```

This command tells otter that we have a Gradescope export located in the `./notebooks` directory with tests in the `./tests` directory and that we want output in the `./outputs` directory. It also tells otter to include verbose output with the `-v` flag.

The output of the command line tool is a CSV file which contains one row for each student and lists the student's identifier, the filename of their submission, and their final grade. This CSV file is output as `OUTPUT-PATH/final_grades.csv`, where `OUTPUT-PATH` is the value passed to the `-o` flag (defaults to `./`). _We are currently working on a feature that will also add columns for each individual test case to provide a score breakdown._

#### Installing Requirements

The Docker image for the grader comes with the following Python packages installed along with their dependencies:

* datascience
* jupyter_client
* ipykernel
* matplotlib
* pandas
* ipywidgets
* scipy
* gofer-grader==1.0.3
* nb2pdf==0.0.1
* otter-grader==0.0.6

If you require packages other than these, place them in a `requirements.txt` file and pass the path to this file to the `-r` flag, e.g.

```
otter -j meta.json -r requirements.txt
```

#### PDF Generation

The otter `Notebook` API includes a method to generate manual-graded PDF submissions, but the command line interface also provides this functionality. To generate PDFs of all notebooks run through the grader, pass the `--pdf` flag to otter:

```
otter -j meta.json --pdf
```

This will create a subdirectory `manual_submissions/` of the current working directory and put the PDF exports of each notebook into this directory, leaving the filename unchanged (with the exception of the extension); e.g., `lab01-123456.ipynb` would be `lab01-123456.pdf`.

Given the time and execution cost of generating all of the PDFs at once, if you are distributing the in-notebook checker from otter, _it is recommended that you have students generate and upload their own PDF submissions_.
