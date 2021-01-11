# Generating Configuration Files

```eval_rst
.. toctree::
   :maxdepth: 1
   :hidden:

   container_image
```

This section details how to generate the configuration files needed for preparing Otter autograders. Note that this step can be accomplished automatically if you're using [Otter Assign](../../otter_assign/index.md).

To use Otter to autograde an assignment, you must first generate a zip file that Otter will use to create a Docker image with which to grade submissions. Otter's command line utility `otter generate` allows instructors to create this zip file from their machines.

## Before Using Otter Generate

Before using Otter Generate, you should already have written [tests](../../test_files/index.md) for the assignment and collected extra requirements into a requirements.txt file (see [here](container_image.md)). (Note: the default requirements can be overwritten by your requirements by passing the `--overwrite-requirements` flag.)

## Directory Structure

For the rest of this page, assume that we have the following directory structure:

```
| hw00-dev
  | - data.csv
  | - hw00-sol.ipynb
  | - hw00.ipynb
  | - requirements.txt
  | - utils.py
  | tests
    | - q1.py
    | - q2.py
    ...
  | hidden-tests
    | - q1.py
    | - q2.py
    ...
```

Also assume that we have `cd`ed into `hw00-dev`.

## Usage

The general usage of `otter generate` is to create a zip file at some output directory (`-o` flag, default `./`) which you will then use to create the grading image. Otter Generate has a few optional flags, described in the [Otter CLI Reference](../../cli_reference.md).

If you do not specify `-t` or `-o`, then the defaults will be used. If you do not specify `-r`, Otter looks in the working directory for `requirements.txt` and automatically adds it if found; if it is not found, then it is assumed there are no additional requirements. There is also an optional positional argument that goes at the end of the command, `files`, that is a list of any files that are required for the notebook to execute (e.g. data files, Python scripts). To autograde an R assignment, pass the `-l r` flag to indicate that the language of the assignment is R.

The simplest usage in our example would be

```
otter generate
```

This would create a zip file `autograder.zip` with the tests in `./tests` and no extra requirements or files. If we needed `data.csv` in the notebook, our call would instead become

```
otter generate data.csv
```

Note that if we needed the requirements in `requirements.txt`, our call wouldn't change, since Otter automatically found `./requirements.txt`.

Now let's say that we maintained to different directories of tests: `tests` with public versions of tests and `hidden-tests` with hidden versions. Because I want to grade with the hidden tests, my call then becomes

```
otter generate -t hidden-tests data.csv
```

Now let's say that I need some functions defined in `utils.py`; then I would add this to the last part of my Otter Generate call:

```
otter generate -t hidden-tests data.csv utils.py
```

If this was instead an R assignment, I would run

```
otter generate -t hidden-tests -l r data.csv
```

## Grading Configurations

There are several configurable behaviors that Otter supports during grading. Each has default values, but these can be configured by creating an Otter config JSON file and passing the path to this file to the `-c` flag (`./otter_config.json` is automatically added if found and `-c` is unspecified).

The support keys and their default values are provided in `otter.run.run_autograder.constants.DEFAULT_OPTIONS`:

```eval_rst
.. ipython:: python

  from otter.run.run_autograder.constants import DEFAULT_OPTIONS
  DEFAULT_OPTIONS
```

### Grading with Environments

Otter can grade assignments using saved environments in the log in the Gradescope container. _This behavior is not supported for R assignments._ This works by deserializing the environment stored in each check entry of Otter's log and grading against it. The notebook is parsed and only its import statements are executed. For more inforamtion about saving and using environments, see [Logging](../../logging.md).

To configure this behavior, two things are required:

* the use of the `grade_from_log` key in your config JSON file
* providing studens with an [Otter configuration file](../../otter_check/dot_otter_files.md) that has `save_environments` set to `true`

This will tell Otter to shelve the global environment each time a student calls `Notebook.check` (pruning the environments of old calls each time it is called on the same question). When the assignment is exported using `Notebook.export`, the log file (at `./.OTTER_LOG`) is also exported with the global environments. These environments are read in in the Gradescope container and are then used for grading. Because one environment is saved for each check call, variable name collisions can be averted, since each question is graded using the global environment at the time it was checked. Note that any requirements needed for execution need to be installed in the Gradescope container, because Otter's shelving mechanism does not store module objects.

### Autosubmission of Notebook PDFs

Otter Generate allows instructors to automatically generate PDFs of students' notebooks and upload these as submissions to a separate Gradescope assignment. This requires a Gradescope token, for which you will be prompted to enter your Gradescope account credentials. Otter Generate also needs the course ID and assignment ID of the assignment to which PDFs should be submitted. This information can be gathered from the assignment URL on Gradescope:

```
https://www.gradescope.com/courses/{COURSE ID}/assignments/{ASSIGNMENT ID}
```

To configure this behavior, set the `course_id` and `assignment_id` configurations in your config JSON file. When Otter Generate is run, you will be prompted to enter your Gradescope email and password. Alternatively, you can provide these via the command-line with the `--username` and `--password` flags, respectively:

```
otter generate --username someemail@domain.com --password thisisnotasecurepassword
```

Currently, this action supports [HTML comment filtering](../../pdfs.md) with pagebreaks, but these can be disabled with the `filtering` and `pagebreaks` keys of your config.

### Pass/Fail Thresholds

The configuration generator supports providing a pass/fail threshold. A threshold is passed as a float between 0 and 1 such that if a student receives at least that percentage of points, they will receive full points as their grade and 0 points otherwise. 

The threshold is specified with the `threshold` key:

```json
{
  "threshold": 0.25
}
```

For example, if a student passes a 2- and 1- point test but fails a 4-point test (a 43%) on a 25% threshold, they will get all 7 points. If they only pass the 1-point test (a 14%), they will get 0 points.

### Overriding Points Possible

By default, the number of points possible on Gradescope is the sum of the point values of each test. This value can be overrided, however, to some other value using the `points` key, which accepts an integer. Then the number of points awarded will be the provided points value scaled by the percentage of points awarded by the autograder.

For example, if a student passes a 2- and 1- point test but fails a 4-point test, they will receive (2 + 1) / (2 + 1 + 4) * 2 = 0.8571 points out of a possible 2 when `--points` is set to 2.

As an example, the command below scales the number of points to 3:

```json
{
  "points": 3
}
```

### Intercell Seeding

The autograder supports intercell seeding with the use of the `seed` key. _This behavior is not supported for Rmd and R script assignments, but is supported for R Jupyter notebooks._ Passing it an integer will cause the autograder to seed NumPy and Python's `random` library or call `set.seed` in R between *every* pair of code cells. This is useful for writing deterministic hidden tests. More information about Otter seeding can be found [here](../../seeding.md). As an example, you can set an intercell seed of 42 with

```json
{
  "seed": 42
}
```

### Showing Autograder Results

The generator allows intructors to specify whether or not the stdout of the grading process (anything printed to the console by the grader or the notebook) is shown to students. **The stdout includes a summary of the student's test results, including the points earned and possible of public _and_ hidden tests, as well as the visibility of tests as indicated by `test["hidden"]`.** 

This behavior is turned off by default and can be turned on by setting `show_stdout` to `true`.

```json
{
  "show_stdout": true
}
```

If `show_stdout` is passed, the stdout will be made available to students _only after grades are published on Gradescope_. The same can be done for hidden test outputs using the `show_hidden` key.

The [Grading on Gradescope](../executing_submissions/gradescope.md) section details more about how output on Gradescope is formatted. Note that this behavior has no effect on any platform besides Gradescope.

### Plugins

To use plugins during grading, list the plugins and their configurations in the `plugin`  key of your config. If a plugin requires no configurations, it should be listed as a string. If it does, it should be listed as a dictionary with a single key, the plugin name, that maps to a subdictionary of configurations.

```json
{
  "plugins": [
    "somepackage.SomeOtterPlugin",
    {
      "somepackage.SomeOtherOtterPlugin": {
        "some_config_key": "some_config_value"
      }
    }
  ]
}
```

For more information about Plugins, see [here](../../plugins/index.md).

## Generating with Otter Assign

Otter Assign comes with an option to generate this zip file automatically when the distribution notebooks are created via the `generate` key of the assignment metadata. See [Distributing Assignments](../../otter_assign/index.md) for more details.
