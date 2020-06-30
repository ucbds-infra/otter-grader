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

## Logging Environments

Whenever a student runs a check cell, Otter can store their current global environment as a part of the log. The purpose of this is twofold: 1) to allow the grading of assignments to occur based on variables whose creation requires access to resources not possessed by the grading environment, and 2) to allow instructors to debug students' assignments by inspecting their global environment at the time of the check. **This behavior must be preconfigured with an [Otter configuration file](dot_otter_files.md) that has its `save_environment` key set to `true`.**

Shelving is accomplished by using the dill library to pickle (almost) everything in the global environment, with the notable exception of modules (so libraries will need to be reimported in the instructor's environment). The environment (a dictionary) is pickled and the resulting file is then stored as a byte string in one of the fields of the log entry.

Environments can be saved to a log entry by passing the environment (as a dictionary) to `LogEntry.shelve`. Any variables that can't be shelved (or are ignored) are added to the `unshelved` attribute of the entry.

```python
from otter.logs import LogEntry
entry = LogEntry()
entry.shelve(globals())
```

To retrieve a shelved environment from an entry, use the `LogEntry.unshelve` method. During the process of unshelving, all functions have their `__globals__` updated to include everything in the unshelved environment and, optionally, anything in the environment passed to `global_env`.

```python
>>> env = entry.unshelve() # this will have everything in the shelf in it -- but not factorial
>>> from math import factorial
>>> env_with_factorial = entry.unshelve({"factorial": factorial}) # add factorial to all fn __globals__
>>> "factorial" in env_with_factorial["some_fn"].__globals__
True
>>> factorial is env_with_factorial["some_fn"].__globals__["factorial"]
True
```

See the reference [below](#otter-logs-reference) for more information about the arguments to `LogEntry.shelve` and `LogEntry.unshelve`.

<!-- TODO: describe variables dict arg -->

## Debugging with the Log

The log is useful to help students debug tests that they are repeatedly failing. Log entries store any errors thrown by the process tracked by that entry and, if the log is a call to `otter.Notebook.check`, also the test results. Any errors held by the log entry can be re-thrown by calling `LogEntry.raise_error`:

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

<!-- TODO: change this to grading from serialized environments -->
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

## Otter Logs Reference

### `otter.logs.Log`

```eval_rst
.. autoclass:: otter.logs.Log
    :members:
```

### `otter.logs.LogEntry`

```eval_rst
.. autoclass:: otter.logs.LogEntry
    :members:
```

### `otter.logs.EventType`

```eval_rst
.. autoclass:: otter.logs.EventType
    :members:
```
