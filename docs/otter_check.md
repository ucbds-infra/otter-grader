# Student Usage: `otter check` and `otter.Notebook`

Otter provides an IPython API and a command line tool that allow students to run checks and export notebooks within the assignment environment.

## The `Notebook` API

Otter supports in-notebook checks so that students can check their progress when working through assignments via the `otter.Notebook` class. The `Notebook` takes one optional parameter that corresponds to the path from the current working directory to the directory of tests; the default for this path is `./tests`.

```python
import otter
grader = otter.Notebook()
```

If my tests were in `./hw00-tests`, then I would instantiate with

```python
grader = otter.Notebook("hw00-tests")
```

Students can run tests in the test directory using `Notebook.check` which takes in a questio identifier (the file name without the `.py` extension) For example,

```python
grader.check("q1")
```

will run the test `q1.py` in the tests directory. If a test passes, then the cell displays "All tests passed!" If the test fails, then the details of the first failing test are printed out, including the test code, expected output, and actual output:

![](images/student_usage_failed_test.png)

Students can also run all tests in the tests directory at once using `Notebook.check_all`:

```python
grader.check_all()
```

This will rerun all tests against the current global environment and display the results for each tests concatenated into a single HTML output. It is recommended that this cell is put at the end of a notebook for students to run before they submit so that students can ensure that there are no variable name collisions, propagating errors, or other things that would cause the autograder to fail a test they should be passing.

Students can also use the `Notebook` class to generate their own PDFs for manual grading using the static method `Notebook.export`. `Notebook.export` has a required positional argument of the path to the notebook to be exported (usually the notebook that students are working through). There are also two optional arguments related to filtering cells: `filtering` indicates whether or not to filter notebooks and defaults to `True`, and `filter_type` indicates the filter type (`"tags"` or `"html"`) to use and defaults to `"html"`. You can find more information about PDF generation [here](pdfs.md).

Because `Notebook.export` is a static method, it can be called either from the class as `otter.Notebook.export()` or from the grader instance as `grader.export()`. We use the latter convetion in the examples below.

As an example, if I wanted to export `hw01.ipynb` with HTML comment filtering, my call would be

```python
grader.export("hw01.ipynb")
```

as filtering is by defult on and the default filtering behavior is HTML comments. If I instead wanted to filter with cell tags, I would call

```python
grader.export("hw01.ipynb", filter_type="tags")
```

Lastly, if I wanted to generate a PDF with no filtering, I would use

```python
grader.export("hw01.ipynb", filtering=False)
```

We don't need to specify a `filter_type` argument here because it would be ignored by the fact that `filtering=False`.

## Command Line Script Checker

Otter also features a command line tool that allows students to run checks on Python files from the command line. `otter check` takes one required argument, the path to the file that is being checked, and two optional flags:

* `-t` is the path to the directory of tests. If left unspecified, it is assumed to be `./tests`
* `-q` is the identifier of a specific question to check (the file name without the `.py` extension). If left unspecified, all tests in the tests directory are run.

The recommended file structure for using the checker is something like the one below:

```
| hw00
  | - hw00.py
  | tests
    | - q1.py
    | - q2.py
    ...
```

After `cd`ing into `hw00`, if I wanted to run the test q2.py, I would run

```
$ otter check hw00.py -q q2
All tests passed!
```

In the example above, I passed all of the tests. If I had failed any of them, I would get an output like that below:

```
$ otter check hw00.py -q q2
1 of 2 tests passed

Tests passed:
 possible 


Tests failed: 
*********************************************************************
Line 2, in tests/q2.py 0
Failed example:
    1 == 1
Expected:
    False
Got:
    True
```

To run all tests at once, I would run

```
$ otter check hw00.py
Tests passed:
 q1  q3  q4  q5 


Tests failed: 
*********************************************************************
Line 2, in tests/q2.py 0
Failed example:
    1 == 1
Expected:
    False
Got:
    True
```

As you can see, I passed for of the five tests above, and filed q2.py.

If I instead had the directory structure below (note the new tests directory name)

```
| hw00
  | - hw00.py
  | hw00-tests
    | - q1.py
    | - q2.py
    ...
```

then all of my commands would be changed by adding `-t hw00-tests` to each call. As an example, let's rerun all of the tests again:

```
$ otter check hw00.py -t hw00-tests
Tests passed:
 q1  q3  q4  q5 


Tests failed: 
*********************************************************************
Line 2, in hw00-tests/q2.py 0
Failed example:
    1 == 1
Expected:
    False
Got:
    True
```
