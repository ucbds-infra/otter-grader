# Tutorial

This tutorial can help you to verify that you have installed Otter correctly and introduce you to the general Otter workflow. Once you have [installed](index.md) Otter, download [this zip file](_static/tutorial.zip) and unzip it into some directory on your machine; you should have the following directory structure:

```
tutorial
├── demo.ipynb
├── meta.json
├── requirements.txt
└── submissions
    ├── ipynbs
    │   ├── demo-fails1.ipynb
    │   ├── demo-fails2.ipynb
    │   ├── demo-fails2Hidden.ipynb
    │   ├── demo-fails3.ipynb
    │   ├── demo-fails3Hidden.ipynb
    │   └── demo-passesAll.ipynb
    └── zips
        ├── demo-fails1.zip
        ├── demo-fails2.zip
        ├── demo-fails2Hidden.zip
        ├── demo-fails3.zip
        ├── demo-fails3Hidden.zip
        └── demo-passesAll.zip
```

This section describes the basic execution of Otter's tools using the provided zip file. It is meant to verify your installation and too _loosely_ describe how Otter tools are used. This section includes Otter Assign, Otter Generate, and Otter Grade.

## Otter Assign

Start by `cd`ing into `tutorial`. This directory includes the master notebook `demo.ipynb`. Look over this notebook to get an idea of its structure. It contains five questions, four code and one Markdown (two of which are manually-graded). Also note that the assignment configuration in the first cell tells Otter Assign to generate a solutions PDF and a Gradescope autograder zip file and to include special submission instructions before the export cell. To run Otter Assign on this notebook, run

```console
$ otter assign demo.ipynb dist
Generating views...
Generating solutions PDF...
Generating autograder zipfile...
Running tests...
All tests passed!
```

Otter Assign should create a `dist` directory which contains two further subdirectories: `autograder` and `student`. The `autograder` directory contains the Gradescope autograder, solutions PDF, and the notebook with solutions. The `student` directory contains just the sanitized student notebook. Both contain a `tests` subdirectory that contains tests, but only `autograder/tests` has the hidden tests.

```
tutorial/dist
├── autograder
│   ├── autograder.zip
│   ├── demo-sol.pdf
│   ├── demo.ipynb
│   ├── otter_config.json
│   └── requirements.txt
└── student
    └── demo.ipynb
```

For more information about the configurations for Otter Assign and its output format, see [Distributing Assignments](otter_assign/index.md).

## Otter Generate

In the `dist/autograder` directory created by Otter Assign, there should be a file called `autograder.zip`. This file is the result of using Otter Generate to generate a zip file with all of your tests and requirements, which is done invisibly by Otter Assign when it is used. Alternatively, you could generate this zip file yourself from the contents of `dist/autograder` by running

```
otter generate
```

in that directory (but this is not recommended).

## Otter Grade

**Note:** You should complete the Otter Assign tutorial above before running this tutorial, as you will need some of its output files.

At this step of grading, the instructor faces a choice: where to grade assignments. The rest of this tutorial details how to grade assignments locally using Docker containers on the instructor's machine. You can also grade on Gradescope or without containerization, as described in the [Executing Submissions](workflow/executing_submissions/index.md) section.

In the zip file, we have provided a [metadata file](workflow/executing_submissions/otter_grade.html#metadata) that maps student identifiers to filenames in `meta.json`. Note that metadata files are optional when using Otter, but we have provided one here to demonstrate their use. This metadata file lists _only_ the files in the `ipynbs` subdirectory, so we won't use it when grading `zips`.

```json
[
    {
        "identifier": "passesAll",
        "filename": "demo-passesAll.ipynb"
    },
    {
        "identifier": "fails1",
        "filename": "demo-fails1.ipynb"
    },
    {
        "identifier": "fails2",
        "filename": "demo-fails2.ipynb"
    },
    {
        "identifier": "fails2Hidden",
        "filename": "demo-fails2Hidden.ipynb"
    },
    {
        "identifier": "fails3",
        "filename": "demo-fails3.ipynb"
    },
    {
        "identifier": "fails3Hidden",
        "filename": "demo-fails3Hidden.ipynb"
    }
]
```

The filename and identifier of each notebook indicate which tests should be failing; for example, `demo-fails2.ipynb` fails all cases for `q2` and `demo-fails2Hidden.ipynb` fails the hidden test cases for `q2`.

Let's now construct a call to Otter that will grade these notebooks. We will use `dist/autograder/autograder.zip` from running Otter Assign to configure our grading image. We also know that we have JSON-formatted metadata, so we'll be use the `-j` metadata flag. Our notebooks are in the `ipynbs` subdirectory, so we'll need to use the `-p` flag. The notebooks also contain a couple of written questions, and the [filtering](pdfs.md) is implemented using HTML comments, so we'll specify the `--pdfs` flag to indicate that Otter should grab the PDFs out of the Docker containers.

Let's run Otter on the notebooks:

```console
otter grade -p submissions/ipynbs -a dist/autograder/autograder.zip -j meta.json --pdfs -v
```

(I've added the `-v` flag so that we get verbose output.) After this finishes running, there should be a new file and a new folder in the working directory: `final_grades.csv` and `submission_pdfs`. The former should contain the grades for each file, and should look something like this:

```
q1 - 1,q1 - 2,q1 - 3,q2 - 1,q2 - 2,q3 - 1,q3 - 2,q3 - 3,q3 - 4,q3 - 5,q3 - 6,q3 - 7,q3 - 8,file
0.3333333333333333,0.3333333333333333,0.3333333333333333,0.5,0.5,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,demo-passesAll.zip
0.3333333333333333,0.3333333333333333,0.3333333333333333,0.0,0.0,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,demo-fails2.zip
0.3333333333333333,0.3333333333333333,0.3333333333333333,0.5,0.5,0.125,0.125,0.125,0.125,0.0,0.0,0.0,0.0,demo-fails3Hidden.zip
0.3333333333333333,0.3333333333333333,0.0,0.5,0.5,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,demo-fails1.zip
0.3333333333333333,0.3333333333333333,0.3333333333333333,0.5,0.5,0.125,0.125,0.125,0.0,0.0,0.0,0.0,0.0,demo-fails3.zip
0.3333333333333333,0.3333333333333333,0.3333333333333333,0.5,0.0,0.125,0.125,0.125,0.125,0.125,0.125,0.125,0.125,demo-fails2Hidden.zip

```

Let's make that a bit prettier:

| file                  | q1 - 1             | q1 - 2             | q1 - 3             | q2 - 1 | q2 - 2 | q3 - 1 | q3 - 2 | q3 - 3 | q3 - 4 | q3 - 5 | q3 - 6 | q3 - 7 | q3 - 8 |
|-----------------------|--------------------|--------------------|--------------------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| demo-passesAll.zip    | 0.3333333333333333 | 0.3333333333333333 | 0.3333333333333333 | 0.5    | 0.5    | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  |
| demo-fails2.zip       | 0.3333333333333333 | 0.3333333333333333 | 0.3333333333333333 | 0.0    | 0.0    | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  |
| demo-fails3Hidden.zip | 0.3333333333333333 | 0.3333333333333333 | 0.3333333333333333 | 0.5    | 0.5    | 0.125  | 0.125  | 0.125  | 0.125  | 0.0    | 0.0    | 0.0    | 0.0    |
| demo-fails1.zip       | 0.3333333333333333 | 0.3333333333333333 | 0.0                | 0.5    | 0.5    | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  |
| demo-fails3.zip       | 0.3333333333333333 | 0.3333333333333333 | 0.3333333333333333 | 0.5    | 0.5    | 0.125  | 0.125  | 0.125  | 0.0    | 0.0    | 0.0    | 0.0    | 0.0    |
| demo-fails2Hidden.zip | 0.3333333333333333 | 0.3333333333333333 | 0.3333333333333333 | 0.5    | 0.0    | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  | 0.125  |

The latter, the `submission_pdfs` directory, should contain the filtered PDFs of each notebook (which should be relatively similar).

Otter Grade can also grade the zip file exports provided by the `Notebook.export` method. **Before grading the zip files, you must edit your `autograder.zip` to incdicate that you're doing so.** To do this, open `demo.ipynb` (the file we used with Otter Assign) and edit the first cell of the notebook (beginning with `BEGIN ASSIGNMENT`) so that the `zips` key under `generate` is `true` in the YAML and rerun Otter Assign.

Now, all we need to do is add the `-z` flag to the call to indicate that you're grading these zip files. We have provided some, with the same notebooks as above, in the `zips` directory, so let's grade those:

```console
otter grade -p submissions/zips -a dist/autograder/autograder.zip -vz
```

This should have the same CSV output as above but no `submission_pdfs` directory since we didn't tell Otter to generate PDFs.

You can learn more about the grading workflow for Otter in [this section](workflow/index.md).
