# Otter-Grader Documentation [OUTDATED]

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

_Note:_ With this setup, you will need to pass in a custom docker image name when using the CLI (see [below](#custom-docker-images)).

## Usage

### Notebook Design: PDF Generation

Otter-grader uses nb2pdf to generate manual submissions as PDFs. When generating the PDF, the following cells will be included by default:

* Markdown cells
* Code cells with images in the output
* All cells tagged with `include`

If a cell falls within one of the 3 categories listed above but you do not want to include it in the exported PDF, tag the cell with `ignore`. This cell will then not be added to the manual graded PDF.

### Ok-Formatted Tests

You can use [https://oktests.herokuapp.com/](https://oktests.herokuapp.com/) to generate your tests in the ok format. Place all generated test files in the tests directory. 

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

```python
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

This will create a file called `lab01.pdf` in the notebook's directory which students can submit. For more information on how nb2pdf filters cells, see the [Notebook Design](#notebook-design-pdf-generation) section.

### Command Line Usage

The help entry for the `otter` command is given below.

```
usage: otter [-h] [-g] [-c] [-j JSON] [-y YAML] [-n NOTEBOOKS-PATH]
             [-t TESTS-PATH] [-o OUTPUT-PATH] [-v] [-r REQUIREMENTS]
             [--containers NUM-CONTAINERS] [--pdf] [--image IMAGE]

optional arguments:
  -h, --help            show this help message and exit
  -g, --gradescope      Flag for Gradescope export
  -c, --canvas          flag for Canvas export
  -j JSON, --json JSON  Flag for path to JSON metadata
  -y YAML, --yaml YAML  Flag for path to YAML metadata
  -n NOTEBOOKS-PATH, --notebooks-path NOTEBOOKS-PATH
                        Path to directory of notebooks
  -t TESTS-PATH, --tests-path TESTS-PATH
                        Path to directory of tests
  -o OUTPUT-PATH, --output-path OUTPUT-PATH
                        Path to which to write output
  -v, --verbose         Flag for verbose output
  -r REQUIREMENTS, --requirements REQUIREMENTS
                        Flag for Python requirements file path
  --containers NUM-CONTAINERS
                        Specify number of containers to run in parallel
  --pdf                 Create PDFs as manual-graded submissions
  --image IMAGE         Custom docker image to run on
```

Using otter requires a metadata file, which can be set for Gradescope (`-g`) or Canvas (`-c`) exports, JSON format (`-j`), or YAML format (`-y`). The JSON and YAML flags require an argument corresponding to the name of the metadata file _relative to the `NOTEBOOKS-PATH` argument_. Note that you can only specify ONE (1) of the metadata flags. The defaults for certain flags are given below.

| Flag | Default Value |
|------|---------------|
| `-n` | `./`, the current working directory |
| `-t` | `./tests`, the `tests` subdirectory of the current working directory |
| `-o` | `./`, the current working directory |

Otter executes the notebooks in parallel Docker containers. Depending on the number and size of the notebooks you are grading, you may wish to change the default number of containers (4) so that your grading can be executed quicker. To do this, pass the number of containers you want created to the `--containers` flag.

An example command would be

```
otter -g -n ./notebooks -t ./tests -o ./outputs --containers 6 -v
```

This command tells otter that we have a Gradescope export located in the `./notebooks` directory with tests in the `./tests` directory and that we want output in the `./outputs` directory. It also tells otter to spin up 6 (rather than 4) docker containers and to include verbose output with the `-v` flag.

The output of the command line tool is a CSV file which contains one row for each student and lists the student's identifier, the filename of their submission, their score breakdown by test case, and their final grade. This CSV file is output as `OUTPUT-PATH/final_grades.csv`, where `OUTPUT-PATH` is the value passed to the `-o` flag (defaults to `./`).

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
* nb2pdf==0.0.2
* otter-grader==0.0.19

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

#### Custom Docker Images

It is possible to use a custom Docker image to execute the notebooks, but it must include the Python packages listed above, along with pandoc and xetex (if you intend to generate PDFs). To use a custom image, pass the image name to the `--image` flag when calling otter. For example,

```
otter -y meta.yml --image my_docker_image
```

### Gradescope Compatibility

Otter is compatible with the Gradescope autograder, and has a command line tool to generate the zipfile that is used to configure the Docker container that Gradescope's autograder usage. The base command for this utility is `otter gen`, and its help entry is given below.


```
usage: otter gen [-h] [-t [TESTS-PATH]] [-o [OUTPUT-PATH]] [-r [REQUIREMENTS]]
             [files [files ...]]

Generates zipfile to configure Gradescope autograder

positional arguments:
  files                 Other support files needed for grading (e.g. .py
                        files, data files)

optional arguments:
  -h, --help            show this help message and exit
  -t [TESTS-PATH], --tests-path [TESTS-PATH]
                        Path to test files
  -o [OUTPUT-PATH], --output-path [OUTPUT-PATH]
                        Path to which to write zipfile
  -r [REQUIREMENTS], --requirements [REQUIREMENTS]
                        Path to requirements.txt file
```

The `otter gen` command creates a zipfile at `OUTPUT-PATH/autograder.zip` which contains the necessary files for the Gradescope autograder:

* `run_autograder`: the script that executes otter
* `setup.sh`: a file that instructs Ubuntu on how to install dependencies
* `requirements.txt`: Python's list of necessary dependencies
* `tests`: the folder of test cases
* `files`: a folder containing any files needed for the notebooks to execute (e.g. data files)

The requirements file create automatically includes the otter dependencies (see [Installing Requirements](#installing-requirements)), but you can optionally include your own, other ones by passing a filepath to the `-r` flag. Any files included that are not passed to a flag are automatically placed into the `files` folder in the zipfile and will be copied into the notebook directory in the Gradescope container.

An example command would be

```
otter gen -t ./hidden-tests -r requirements.txt my_data.csv my_other_data.json utils.py
```

This tells `otter gen` to copy the tests from `./hidden-tests`, add the requirements from `./requirements.txt`, and to include the files `my_data.csv`, `my_other_data.json`, and `utils.py`. All of these files will be made available to the notebook when it is executed.

#### Relative Imports on Gradescope

Because of the way that the Gradescope autograder is set up, our script must change relative import syntax in order to ensure that the necessary files are loaded. **Because we cannot differentiate between package imports and relative imports, `otter gen` automatically assumes that if you are importing a .py file that it is called `utils.py`.** The regex used to change the import syntax will _only_ change the syntax if you're using the import statment

```python
from utils import *
```

For this reason, if you have any functions you need in a file that is going to be imported, _make sure that it is called `utils.py`._
