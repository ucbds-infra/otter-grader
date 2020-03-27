# Grading Locally: `otter grade`

The command line interface allows instructors to grade notebooks locally by launching Docker containers on the instructor's machine that grade notebooks and return a CSV of grades and (optionally) PDF versions of student submissions for manually graded questions.

## Prerequisites

Before using the command line utility, you should have

* written tests for the assignment
* downloaded submissions into a directory
* written a [metadata file](metadata_files.md) if not using a Gradescope or Canvas export

## Using the CLI

<!-- ### The `otter` Command -->

The grading interface, encapsulated in the `otter grade` command, runs the local grading process and defines the options that instructors can set when grading. A comprehensive list of flags is provided below.

| Flag | Default Value | Description |
|-----|-----|-----|
| `-h`, `--help` |  | Show help message and exit |
| `-p`, `--path` | `./` | Path to directory of submissions |
| `-t`, `--tests-path` | `./tests` | Path to directory of tests |
| `-o`, `--output-path` | `./` | Path at which to write output (CSV and directory of PDFs) |
| `-g`, `--gradescope` |  | Indicates a Gradescope export format for submissions|
| `-c`, `--canvas` |  | Indicates a Canvas export format for submissions|
| `-j`, `--json` |  | Path to JSON metadata file |
| `-y`, `--yaml` |  | Path to YAML metadata file |
| `-s`, `--scripts` |  | Indicates that Python scripts are being executed (not IPython notebooks) |
| `--pdf` |  | Generate unfiltered PDFs for manual grading |
| `--tag-filter` |  | Generate PDFs filtered by cell tags for manual grading |
| `--html-filter` |  | Generate PDFs filtered by HTML comments for manual grading |
| `-f`, `--files` |  | Path to any support files needed for execution (e.g. data files) |
| `-v`, `--verbose` |  | Write verbose output to console |
| `-r`, `--requirements` | `./requirements.txt` | Path to requirements.txt file |
| `--containers` | 4 | Number of parallel containers to launch; submissions will be divided evenly among them |
| `--image` | ucbdsinfra/otter-grader | Docker image on which to grade submissions |
| `--no-kill` |  | Prevents containers from being killed after execution for debugging |

### Basic Usage

The simplest usage of the `otter grade` command is when we have a directory structure as below (and we have `cd`ed into `grading` in the command line) and we don't require PDFs or additional requirements.

```
| grading
  | - meta.yml
  | - nb0.ipynb
  | - nb1.ipynb
  | - nb2.ipynb
  ...
  | tests
    | - q1.py
    | - q2.py
    | - q3.py
    ...
```

In the case above, our otter command would be, very simply,

```
otter grade -y meta.yml
```

Because the submissions are on the current working directory (`grading`), our tests are at `./tests`, and we don't mind output to `./`, we can use the defualt values of the `-p`, `-t`, and `-o` flags, leaving the only necessary flag the metadata flag. Since we have a YAML metadata file, we specify `-y` and pass the path to the metadata file, `./meta.yml`.

After grader, our directory will look like this:

```
| grading
  | - final_grades.csv
  | - meta.yml
  | - nb0.ipynb
  | - nb1.ipynb
  | - nb2.ipynb
  ...
  | tests
    | - q1.py
    | - q2.py
    | - q3.py
    ...
```

and the grades for each submission will be in `final_grades.csv`.

If we wanted to generate PDFs for manual grading, we would specify one of the three PDF flags:

```
otter grade -y meta.yml --pdf
```

and at the end of grading we would have

```
| grading
  | - final_grades.csv
  | - meta.yml
  | - nb0.ipynb
  | - nb1.ipynb
  | - nb2.ipynb
  ...
  | manual_submissions
    | - nb0.pdf
    | - nb1.pdf
    | - nb2.pdf
    ...
  | tests
    | - q1.py
    | - q2.py
    | - q3.py
    ...
```

### Metadata Flags

The four metadata flags, `-g`, `-c`, `-j`, and `-y`, correspond to different export/metadata file formats. Also note that the latter two require you to specify a path to the metadata file. You must specify a metadata flag every time you run `otter grade`, and you may not specify more than one. For more information about metadata and export formats, see [this page](metadata_files.md).

### Requirements

The `ucbdsinfra/otter-grader` Docker image comes preinstalled with the following Python packages and their dependencies:

* datascience
* jupyter_client
* ipykernel
* matplotlib
* pandas
* ipywidgets
* scipy
* tornado
* nb2pdf
* otter-grader

If you require any packages not listed above, or among the dependencies of any packages above, you should create a requirements.txt file _containing only those packages_. If this file is created in the working directory (i.e. `./requirements.txt`), then Otter will automatically find this file and include it. If this file is not at `./requirements.txt`, pass its path to the `-r` flag.

For example, continuining the example above with the package SymPy, I would create a requirements.txt

```
| grading
  | - meta.yml
  | - nb0.ipynb
  | - nb1.ipynb
  | - nb2.ipynb
  ...
  | - requirements.txt
  | tests
    | - q1.py
    | - q2.py
    | - q3.py
    ...
```

that lists only SymPy

```bash
$ cat requirements.txt
sympy
```

Now my call, using HTML comment filtered PDF generation this time, would become 

```
otter grade -y meta.yml --html-filter
```

Note the lack of the `-r` flag; since I created my requirements file in the working directory, Otter found it automatically.

### Grading Python Scripts

If I wanted to grade Python scripts instead of IPython notebooks, my call to Otter would only add the `-s` flag. Consider the directory structure below:

```
| grading
  | - meta.yml
  | - sub0.py
  | - sub1.py
  | - sub2.py
  ...
  | - requirements.txt
  | tests
    | - q1.py
    | - q2.py
    | - q3.py
    ...
```

My call to grade these submissions would be

```
otter grade -sy meta.yml
```

**Note the lack of a PDF flag,** as it doesn't make sense to convert Python files to PDFs. PDF flags only work when grading IPython Notebooks.

### Support Files

Some notebooks require support files to run (e.g. data files). If your notebooks require any such files, there are two ways to get them into the container so that they are available to notebooks:

* specifying paths to the files with the `-f` flag
* putting them into the notebook path

Suppose that my notebooks in `grading` required `data.csv` in my `../data` directory:

```
| data
  | - data.csv
| grading
  | - meta.yml
  | - nb0.ipynb
  | - nb1.ipynb
  | - nb2.ipynb
  ...
  | - requirements.txt
  | tests
    | - q1.py
    | - q2.py
    | - q3.py
    ...
```

I could pass this data into the container using the call 

```
otter grade -y meta.yml -f ../data/data.csv
```

Or I could move (or copy) `data.csv` into `grading`:

```
$ mv ../data/data.csv ./
```

```
| data
| grading
  | - data.csv
  | - meta.yml
  | - nb0.ipynb
  | - nb1.ipynb
  | - nb2.ipynb
  ...
  | - requirements.txt
  | tests
    | - q1.py
    | - q2.py
    | - q3.py
    ...
```

and then just run Otter as normal:

```
otter grade -y meta.yml
```

All non-notebook files in the notebooks path are copied into all of the containers, so `data.csv` will be made available to all notebooks.
