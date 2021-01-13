# Grading Container Image

When you use Otter Generate to create the configuration zip file for Gradescope, Otter includes the following software and packages for installation. The zip archive, when unzipped, has the following contents:

```
autograder/
| - environment.yml
| - otter_config.json
| - requirements.R
| - requirements.txt
| - run_autograder
| - run_otter.py
| - setup.sh
| files/
  | - ...
| tests/
  | - ...
```

**Note that for pure-Python assignments, `requirements.R` is not included and all of the R-pertinent portions of `setup.sh` are removed.** Below are descriptions of each of the items listed above and the Jinja2 templates used to create them (if applicable).

## `setup.sh`

This file, required by Gradescope, performs the installation of necessary software for the autograder to run. The script template looks like this:

```eval_rst
.. literalinclude:: ../../../otter/generate/templates/r/setup.sh
  :language: shell
```

This script does the following:

1. Install Python 3.7 and pip
2. Install pandoc and LaTeX
3. Install wkhtmltopdf
4. Set Python 3.7 to the default python version
5. Install apt-get dependencies for R
6. Install Miniconda
7. Install R, `r-essentials`, and `r-devtools` from conda
8. Install Python requirements from [`requirements.txt`](#requirements.txt) (this step installs Otter itself)
9. Install R requires from [`requirements.R`](#requirements.R)
10. Install Otter's R autograding package ottr

Currently this script is not customizable, but you can unzip the provided zip file to edit it manually.

## `environment.yml`

This file specifies the conda environment that Otter creates in `setup.sh`.

```eval_rst
.. literalinclude:: ../../../otter/generate/templates/r/environment.yml
  :language: yaml
```

## `requirements.txt`

This file contains the Python dependencies required to execute submissions. It is also the file that your requirements are appended to when you provided your own requirements file   for a Python assignment (unless `--overwrite-requirements` is passed). The template requirements for Python are:

```eval_rst
.. literalinclude:: ../../../otter/generate/templates/python/requirements.txt
```

If you are using R, there will be no additional requirements sent to this template, and `rpy2` will be added. Note that this installs the exact version of Otter that you are working from. This is important to ensure that the configurations you set locally are correctly processed and processable by the version on the Gradescope container. If you choose to overwrite the requirements, _make sure to do the same._ 

## `requirements.R`

This file uses R functions like `install.packages` and `devtools::install_github` to install R packages. If you are creating an R assignment, it is this file (rather than `requirements.txt`) that your requirements and overwrite-requirements options are applied to. The template file contains:

```eval_rst
.. literalinclude:: ../../../otter/generate/templates/r/requirements.R
  :language: r
```

## `run_autograder`

This is the file that Gradescope uses to actually run the autograder when a student submits. Otter provides this file as an executable that activates the conda environment and then calls `/autograder/source/run_otter.py`:

```eval_rst
.. literalinclude:: ../../../otter/generate/templates/r/run_autograder
  :language: shell
```

## `run_otter.py`

This file contains the logic to start the grading process by importing and running `otter.run.run_autograder.main`:

```eval_rst
.. literalinclude:: ../../../otter/generate/templates/r/run_otter.py
  :language: python
```

## `otter_config.json`

This file contains any user configurations for grading. It has no template but is populated with the default values and any updates to those values that a user specifies. When debugging grading via SSH on Gradescope, a helpful tip is to set the `debug` key of this JSON file to `true`; this will stop the autograding from ignoring errors when running students' code, and can be helpful in debugging specific submission issues.

## `tests`

This is a directory containing the test files that you provide. All `.py` (or `.R`) files in the tests directory path that you provide are copied into this directory and are made available to submissions when the autograder runs.

## `files`

This directory, not present in all autograder zip files, contains any support files that you provide to be made available to submissions.
