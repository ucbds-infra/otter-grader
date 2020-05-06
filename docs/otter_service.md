# Deploying a Grading Service

Otter Service is a deployable grading server that students can send submissions to from in the notebook and which will grade submissions based on predefined tests. It is a service packaged with Otter but has additional requirements that are not necessary for running Otter without Otter Service. Otter Service is a tornado server that accepts requests with student submissions, writes the submission to disk, grades them, and saves the grade breakdowns in a Postgres database. This page details how to configure an already-deployed Otter Service instance, and is agnostic of deployment type. For more information on deploying an Otter Service instance, see [here]().

## Configuration Repo

Otter Service is configured to grade assignments through a repository structure. While maintaing a git repo of assignment configurations is not required, it certainly makes editing and updated your assignments easier. Any directory that has the structure described here will do to set up assignments on an Otter Service deployments. If you are grading multiple classes on an Otter Service deployment, you must have one assignments repo for **each** class.

The first and most important file required is the `conf.yml` file, at the root of the repo. This file will define some important configurations and provide paths to the necessary files for each assignment. While the following structure is not required, we recommend something like it to keep a logical structure to the repo.

```
| data-8-assignments
    | - conf.yml
    | - requirements.txt
    | hw
        | hw01
            | - requirements.txt
            | test
                | - q0.py
                | - q1.py
                ...
        | hw02
        ...
    | proj
        | proj01
        ...
    ...
```

### The Configuration File

The `conf.yml` file is a YAML-formatted file that defines the necessary configurations and paths to set up assignments on an Otter Service deployment. It has the following structure:

```yaml
class_name: Data 8      # the name of the course
class_id: data8x        # a **unique** ID for the course
requirements: requirements.txt      # Path to a **global** reuquirements file
assignments:                        # list of assignments
    - name: Project 2               # assignment name
      assignment_id: proj02         # assignment ID, unique among all assignments in this config
      tests_path: proj/proj02/tests                     # path to directory of tests for this assignment
      requirements: proj/proj02/requirements.txt        # path to requirements specific to **this** assignment
      seed: 42                      # random seed for intercell seeding
      files:                        # list of files needed by the autograder, e.g. data files
        - proj/proj02/frontiers1.csv
        - proj/proj02/frontiers2.csv
        - proj/proj02/players.py
    ...
```

Note that the `class_id` must be unique among **all** classes being run on the Otter Service instance, whereas the `assignment_id`s must be unique only within a specific class. Also note that there are two requirements files: a global requirements file that contains requirements not [already in the Docker image](otter_grade.html#requirements) to be installed on **all** assignment images in this config, and an assignment-specific requirements file to be installed **only** in the image for that assignment. Also note that all paths are relative to the root of the assignments repo.

### Other Files

Other files can be included basically anywhere as long as its a subdirectory of the assignments repo, as long as their paths are specified in the `conf.yml` file. The assignments repo should contain any necessary requirements files, all test files, and any support files needed to execute the notebooks (e.g. data files, Python scripts).

## Building the Images

Once you have cloned your assignments repo onto your Otter Service deployment, use the command `otter service build` to add assignments to the database and create their Docker images. Note that it is often necessary to run `otter service build` with `sudo` so that you have the necessary permissions; in this section, assume we have prepended each command with `sudo`.

The builder takes one positional argument that corresponds to the path to the assignments repo; this is assumed to be `./` (i.e. it is assumed to be the working directory). 

## `otter service build` Reference

```eval_rst
.. argparse::
   :module: otter.argparser
   :func: get_parser
   :prog: otter
   :path: service build
   :nodefaultconst:
```
