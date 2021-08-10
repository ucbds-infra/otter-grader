# Usage and Output

Otter Assign is called using the `otter assign` command. This command takes in two required arguments. The first is `master`, the path to the master notebook (the one formatted as described above), and the second is `result`, the path at which output shoud be written. The optional `files` argument takes an arbitrary number of paths to files that should be shipped with notebooks (e.g. data files, images, Python executables). **Otter Assign will automatically recognize the language of the notebook** by looking at the kernel metadata; similarly, if using an Rmd file, it will automatically choose the language as R. This behavior can be overridden using the `-l` flag which takes the name of the language as its argument.

**Note:** The path to the master notebook and to the result directory should be relative to the _working_ directory, but any paths in `files` should be relative to the parent directory of the master notebook. To clarify, the following directory structure:

```
| dev
  | lab
    | lab00
      | - lab00.ipynb
      | data
        | - data.csv
  | dist
    | lab
      | lab00
        # THIS is where we want the results to go
```

would be run through Otter Assign from the `dev` directory with

```
otter assign lab/lab00/lab00.ipynb dist/lab/lab00 data/data.csv
```

The default behavior of Otter Assign is to do the following:

1. Filter test cells from the master notebook and write these to test files
2. Add Otter initialization, export, and `Notebook.check_all` cells
3. Clear outputs and write questions (with metadata hidden), prompts, and solutions to a notebook in a new `autograder` directory
4. Write *all* tests to `autograder/tests`
5. Copy autograder notebook with solutions removed into a new `student` directory
6. Write *public* tests to `student/tests`
7. Copy `files` into `autograder` and `student` directories
8. Run all tests in `autograder/tests` on the solutions notebook to ensure they pass
9. (If `generate` is passed,) generate a Gradescope autograder zipfile from the `autograder` directory

The behaviors described in step 2 can be overridden using the optional arguments described in the help specification.

**An important note:** make sure that you *run all cells* in the master notebook and save it *with the outputs* so that Otter Assign can generate the test files based on these outputs. The outputs will be cleared in the copies generated by Otter Assign.

## Python Output Additions

The following additional cells are included _only_ in Python notebooks.

### Export Formats and Flags

By default, Otter Assign adds an initialization cell at the *top* of the notebook with the contents

```python
# Initialize Otter
import otter
grader = otter.Notebook()
```

To prevent this behavior, add the `--no-init-cell` flag.

Otter Assign also automatically adds a check-all cell and an export cell to the end of the notebook. The check-all cells consist of a Markdown cell:

```
To double-check your work, the cell below will rerun all of the autograder tests.
```

and a code cell that calls `otter.Notebook.check_all`:

```python
grader.check_all()
```

The export cells consist of a Markdown cell:

```
## Submission

Make sure you have run all cells in your notebook in order before running the cell below, so that all images/graphs appear in the output. **Please save before submitting!**
```

and a code cell that calls `otter.Notebook.export` with HTML comment filtering:

```python
# Save your notebook first, then run this cell to export.
grader.export("/path/to/notebook.ipynb")
```

To prevent the inclusion of a check-all cell, use the `--no-check-all` flag. To prevent cell filtering in the export cell, use the `--no-filter` flag. To remove the export cells entirely, use the `--no-export-cell` tag. If you have custom instructions for submission that you want to add to the export cell, pass them to the `--instructions` flag.

**Note:** Otter Assign currently only supports [HTML comment filtering](../pdfs.md). This means that if you have other cells you want included in the export, you must delimit them using HTML comments, not using cell tags.

## Otter Assign Example

Consider the directory stucture below, where `hw00/hw00.ipynb` is an Otter Assign-formatted notebook.

```
| hw00
  | - hw00.ipynb
  | - data.csv
```

To generate the distribution versions of `hw00.ipynb` (after `cd`ing into `hw00`), I would run

```
otter assign hw00.ipynb dist
```

If it was an Rmd file instead, I would run

```
otter assign hw00.Rmd dist
```

This will create a new folder called `dist` with `autograder` and `student` as subdirectories, as described above.

```
| hw00
  | - hw00.ipynb
  | - data.csv
  | dist
    | autograder
      | - hw00.ipynb
      | tests
        | - q1.(py|R)
        | - q2.(py|R)
        ...
    | student
      | - hw00.ipynb
      | tests
        | - q1.(py|R)
        | - q2.(py|R)
        ...
```

If I had wanted to include `data.csv` in the distribution folders, I would change my call to

```
otter assign hw00.ipynb dist data.csv
```

The resulting directory structure would be:

```
| hw00
  | - hw00.ipynb
  | - data.csv
  | dist
    | autograder
      | - data.csv
      | - hw00.ipynb
      | tests
    | student
      | - data.csv
      | - hw00.ipynb
      | tests
```

In generating the distribution versions, I can prevent Otter Assign from rerunning the tests using the `--no-run-tests` flag:

```
otter assign --no-run-tests hw00.ipynb dist data.csv
```

Because tests are not run on R notebooks, the above configuration would be ignored if `hw00.ipynb` had an R kernel.

If I wanted no initialization cell and no cell filtering in the export cell, I would run

```
otter assign --no-init-cell --no-filtering hw00.ipynb dist data.csv
```