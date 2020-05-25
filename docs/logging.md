# Logging

In order to assist with debugging students' checks, Otter automatically logs events when called from `otter.Notebook` or `otter check`. The events are logged in the following methods of `otter.Notebook`:

* `__init__`
* `_auth`
* `check`
* `check_all`
* `export`
* `submit`
* `to_pdf`

The events are stored as `otter.logs.LogEntry` objects which are pickled and appended to a file called `.OTTER_LOG`. To interact with a log, the `otter.logs.Log` class is provided; logs can be read in using the class method `Log.from_file`:

```python
from otter.logs import Log
log = Log.from_file(".OTTER_LOG")
```

The log order defaults to chronological (the order in which they were appended to the file) but this can be reversed by setting the `ascending` argument to `False`. To get the most recent results for a specific question, use `Log.get_results`:

```python
log.get_results("q1")
```

Note that the `otter.logs.Log` class does not support editing the log file, only reading and interacting with it.

## Debugging with the Log

The log is useful to help students debug tests that they are repeatedly failing. Log entries story any errors thrown by the process tracked by that entry and, if the log is a call to `otter.Notebook.check`, also the test results. Any errors held by the log entry can be re-thrown by calling `LogEntry.raise_error`:

```python
from otter.logs import Log
log = Log.from_file(".OTTER_LOG")
entry = log.entries[0]
entry.raise_error()
```

The test results of an entry can be returned using `LogEntry.get_results`:

```python
entry.get_results()
```

## Pregrading Questions

Logs can also be used to pregrade questions. If the grading environment does not have the dependencies necessary to run all code, the results of tests in the log can be used to allow the results of public tests in the students' execution environments to overwrite the grade assignment by the grading environment. For example, if the execution hub has access to a large SQL server that cannot be accessed by a Gradescope grading container, these questions can still be graded (albeit with only public  tests) using the log of checks run by the students. 

To configure these pregraded questions, include an Otter configuration file in the assignment directory that defines the notebook name and the question names that are pregraded. The assignment directory might look like:

```
| hw00
  | - hw00.ipynb
  | - hw00.otter
  | tests
    | - q1.py
    | - q2.py
    | - q3.py
    ...
```

and the `.otter` file would have the following contents (assuming you're not using an Otter Service instance):

```json
{
    "notebook": "hw00.ipynb",
    "pregraded_questions": [
        "q1",
        "q3"
    ]
}
```

This would configure the autograder to grade `q1` and `q3` based on the log and all other questions based on execution results.

## `otter.logs` Reference

```eval_rst
.. automodule:: otter.logs
    :members:
```
