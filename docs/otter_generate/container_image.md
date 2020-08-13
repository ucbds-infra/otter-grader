# Grading Container Image

When you use Otter Generate to create the configuration zip file for Gradescope, Otter includes the following software and packages for installation. The zip archive, when unzipped, has the following contents:

```
autograder/
| - requirements.R
| - requirements.txt
| - run_autograder
| - setup.sh
| files/
  | - ...
| tests/
  | - ...
```

## `setup.sh`

This file, required by Gradescope, performs the installation of necessary software for the autograder to run. The default scripts looks like this:

```sh
#!/usr/bin/env bash

apt-get clean
apt-get update
apt-get install -y python3.7 python3-pip python3.7-dev

apt-get clean
apt-get update
apt-get install -y pandoc
apt-get install -y texlive-xetex texlive-fonts-recommended texlive-generic-recommended

# install wkhtmltopdf
wget --quiet -O /tmp/wkhtmltopdf.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb
apt-get install -y /tmp/wkhtmltopdf.deb

update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

apt-get clean
apt-get update
apt-get install -y install build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev libcurl4-openssl-dev

# install conda
wget -nv -O /autograder/source/miniconda_install.sh "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
chmod +x /autograder/source/miniconda_install.sh
/autograder/source/miniconda_install.sh -b
echo "export PATH=/root/miniconda3/bin:\$PATH" >> /root/.bashrc

export PATH=/root/miniconda3/bin:$PATH
export TAR="/bin/tar"

# install R dependencies
conda install --yes r-base r-essentials 
conda install --yes r-devtools -c conda-forge

# install requirements
pip3 install -r /autograder/source/requirements.txt
pip install -r /autograder/source/requirements.txt
Rscript /autograder/source/requirements.r

# install ottr; not sure why it needs to happen twice but whatever
git clone --single-branch -b stable https://github.com/ucbds-infra/ottr.git /autograder/source/ottr
cd /autograder/source/ottr 
Rscript -e "devtools::install()" || Rscript -e "devtools::install()"
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

## `requirements.txt`

This file contains the Python dependencies required to execute submissions. It is also the file that your requirements are appended to when you provided your own requirements file   for a Python assignment (unless `--overwrite-requirements` is passed). The default requirements are:

```
datascience
jupyter_client
ipykernel
matplotlib
pandas
ipywidgets
scipy
seaborn
sklearn
jinja2
nbconvert
nbformat
dill
rpy2
jupytext
numpy==1.16.0
tornado==5.1.1
git+https://github.com/ucbds-infra/otter-grader.git@bc58bf5a8d13df97e43935c262dd4f2a5c16e075
```

Note that this installs the exact version of Otter that you are working from. This is important to ensure that the configurations you set locally are correctly processed and processable by the version on the Gradescope container. If you choose to overwrite the requirements, _make sure to do the same._

## `requirements.R`

This file uses R functions like `install.packages` and `devtools::install_github` to install R packages. If you are creating an R assignment, it is this file (rather than `requirements.txt`) that your requirements and overwrite-requirements options are applied to. The default file contains:

```R
install.packages(c(
    "usethis",
    "testthat",
    "startup"
), repos="http://cran.us.r-project.org")
```

## `run_autograder`

This is the file that Gradescope uses to actually run the autograder when a student submits. Otter provides this file as a Python executable that defines the configurations for grading in a dictionary and then calls `otter.generate.run_autograder.main`:

```python
#!/usr/bin/env python3

import os
import subprocess

from otter.generate.run_autograder import main as run_autograder

config = {
    "score_threshold": None,
    "points_possible": None,
    "show_stdout_on_release": False,
    "show_hidden_tests_on_release": False,
    "seed": None,
    "grade_from_log": False,
    "serialized_variables": {},
    "public_multiplier": 0,
    "token": None,
    "course_id": 'None',
    "assignment_id": 'None',
    "filtering": True,
    "pagebreaks": True,
    "debug": False,
    "autograder_dir": '/autograder',
    "lang": 'python',
}

if __name__ == "__main__":
    run_autograder(config)
```

When debuggin grading via SSH on Gradescope, a helpful tip is to set the `debug` key of this dict to `True`; this will stop the autograding from ignoring errors when running students' code, and can be helpful in debugging specific submission issues.

## `tests`

This is a directory containing the test files that you provide. All `.py` (or `.R`) files in the tests directory path that you provide are copied into this directory and are made available to submissions when the autograder runs.

## `files`

This directory, not present in all autograder zip files, contains any support files that you provide to be made available to submissions.
