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
│   ├── requirements.txt
│   └── tests
│       ├── q1.py
│       ├── q2.py
│       └── q3.py
└── student
    ├── demo.ipynb
    └── tests
        ├── q1.py
        ├── q2.py
        └── q3.py
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

Otter Grade can also grade the zip file exports provided by the `Notebook.export` method. To do this, just add the `-z` flag to your call to indicate that you're grading these zip files. We have provided some, with the same notebooks as above, in the `zips` directory, so let's grade those:

```console
otter grade -p submissions/zips -a dist/autograder/autograder.zip -vz
```

This should have the same CSV output as above but no `submission_pdfs` directory since we didn't tell Otter to generate PDFs.

You can learn more about the grading workflow for Otter in [this section](workflow/index.md).

<!-- 
## Using Otter

Now that you have verified that your isntallation is working, let's learn more about Otter's general workflow. Otter has two major use cases: grading on the instructor's machine (local grading), and generating files to use Gradescope's autograding infrastructure.

### Local Grading

Get started by creating some [test cases](test_files/index.md) and creating a requirements.txt file (if necessary).

#### Collecting Student Submissions

The first major decision is how you'll collect student submissions. You can collect these however you want, although Otter has builtin compatibility with Gradescope and Canvas. If you choose either Gradescope or Canvas, just export the submissions and unzip that into some directory. If you are collecting another way, you may want to create a metadata file. You can use either JSON or YAML format, and the structure is pretty simple: each element needs to have a filename and a student identifier. Metadata files are optional, and if not provided, grades will be primary keyed on the submission filename. A sample YAML metadata file would be:

```yaml
- identifier: 0
  filename: test-nb-0.ipynb
- identifier: 1
  filename: test-nb-1.ipynb
- identifier: 2
  filename: test-nb-2.ipynb
- identifier: 3
  filename: test-nb-3.ipynb
- identifier: 4
  filename: test-nb-4.ipynb
- identifier: 5
  filename: test-nb-5.ipynb
...
```

#### Support Files

If you have any files that are needed by the notebooks (e.g. data files), put these into the directory that contains the notebooks. You should also have your directory of tests nearby. At this stage, your directory should probably look something like this:

```
| grading
  | - requirements.txt
  | submissions
    | - meta.yml
    | - nb0.ipynb
    | - nb1.ipynb
    | - nb2.ipynb
    | - nb3.ipynb
    | - nb4.ipynb
    | - nb5.ipynb
    | - data.csv
  | tests
    | - q1.py
    | - q2.py
    | - q3.py
    | - q4.py
```

#### Grading

Now that you've set up the directory, let's get down to grading. Go to the terminal, `cd` into your grading directory (`grading` in the example above), and let's build the `otter grade` command. The first thing we need is our notebooks path or `-p` argument. Otter assumes this is `./`, but our notebooks are located in `./submissions`, so we'll need `-p submissions` in our command. We also need a tests directory, which Otter assumes is at `./tests`; because this is where our tests are, we're alright on this front, and don't need a `-t` argument.

Now we need to tell Otter how we've structured our metadata. If you're using a Gradescope or Canvas export, just pass the `-g` or `-c` flag, respectively, with no arguments. If you're using a custom metadata file, as in our example, pass the `-j` or `-y` flag with the path to the metadata file as its argument; in our case, we will pass `-y submissions/meta.yml`.

At this point, we need to make a decision: do we want PDFs? If there are questions that need to be manually graded, it might be nice to generate a PDF of each submission so that it can be easily read; if you want to generate PDFs, pass one of the `--pdfs unfiltered`, `--pdfs tags`, or `--pdfs html` flags (cf. [PDFs](pdfs.md)). For our example, let's say that we *do* want PDFs.

Now that we've made all of these decisions, let's put our command together. Our command is:

```console
otter grade -p submissions -y meta.yml --pdf -v
```

Note that Otter automatically found our requirements file at `./requirements.txt`. If it had been in a different location, we would have needed to pass the path to it to the `-r` flag. Note also that we pass the `-v` flag so that it prints verbose output. Once this command finishes running, you will end up with a new file and a new folder in your working directory:

```
| grading
  | - final_grades.csv
  | - requirements.txt
  | submission_pdfs
    | - nb0.pdf
    | - nb1.pdf
    | - nb2.pdf
    | - nb3.pdf
    | - nb4.pdf
    | - nb5.pdf
  | submissions
    ...
  | tests
    ...
```

Otter created the `final_grades.csv` file with the grades for each student, broken down by test, and the `submission_pdfs` directory to house the PDF that was generated of each notebook.

**Congrats, you're done!** You can use the grades in the CSV file and the PDFs to complete grading however you want.

You can find more information about `otter grade` [here](workflow/executing_submissions/otter_grade.md).

### Gradescope

To get started using Otter with Gradescope, create some [test cases](test_files/index.md) and a requirements.txt file (if necessary). Once you have these pieces in place, put them into a directory along with any additional files that your notebook requires (e.g. data files), for example:

```
| gradescope
  | - data.csv
  | - requirements.txt
  | - utils.py
  | tests
    | - q1.py
    | - q2.py
    ...
```

To create the zipfile for Gradescope, use the `otter generate` command after `cd`ing into the directory you created. For the directory above, once I've `cd`ed into `gradescope`, I would run the following to generate the zipfile:

```
otter generate data.csv utils.py
```

As above, Otter automatically found our requirements file at `./requirements.txt`. Notice also that we didn't indicate the path to the tests directory; this is because the default argument of the `-t` flag is `./tests`, so Otter found them automatically.

After this command finishes running, you should have a file called `autograder.zip` in the current working directory:

```
| gradescope
  | - autograder.zip
  | - data.csv
  | - requirements.txt
  | - utils.py
  | tests
    | - q1.py
    | - q2.py
    ...
```

To use this zipfile, create a Programming Assignment on Gradescope and upload this zipfile on the Configure Autograder page of the assignment. Gradescope will then build a Docker image on which it will grade each student's submission.

You can find more information about Gradescope usage [here](workflow/otter_generate/index.md). -->
