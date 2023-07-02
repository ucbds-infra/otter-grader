.. _logging:

Logging
=======

In order to assist with debugging students' checks, Otter automatically logs events when called from 
``otter.Notebook`` or ``otter check``. The events are logged in the following methods of 
``otter.Notebook``:

* ``__init__``
* ``_auth``
* ``check``
* ``check_all``
* ``export``
* ``submit``
* ``to_pdf``

The events are stored as ``otter.logs.LogEntry`` objects which are pickled and appended to a file 
called ``.OTTER_LOG``. To interact with a log, the ``otter.logs.Log`` class is provided; logs can be 
read in using the class method ``Log.from_file``:

.. code-block:: python

    from otter.check.logs import Log
    log = Log.from_file(".OTTER_LOG")

The log order defaults to chronological (the order in which they were appended to the file) but this 
can be reversed by setting the ``ascending`` argument to ``False``. To get the most recent results 
for a specific question, use ``Log.get_results``:

.. code-block:: python

    log.get_results("q1")

Note that the ``otter.logs.Log`` class does not support editing the log file, only reading and 
interacting with it.


Logging Environments
--------------------

Whenever a student runs a check cell, Otter can store their current global environment as a part of 
the log. The purpose of this is twofold: 1) to allow the grading of assignments to occur based on 
variables whose creation requires access to resources not possessed by the grading environment, and 
2) to allow instructors to debug students' assignments by inspecting their global environment at the 
time of the check. This behavior must be preconfigured with an :ref:`Otter configuration file 
<otter_check_dot_otter_files>` that has its ``save_environment`` key set to ``true``.

Shelving is accomplished by using the dill library to pickle (almost) everything in the global 
environment, with the notable exception of modules (so libraries will need to be reimported in the 
instructor's environment). The environment (a dictionary) is pickled and the resulting file is then 
stored as a byte string in one of the fields of the log entry.

Environments can be saved to a log entry by passing the environment (as a dictionary) to 
``LogEntry.shelve``. Any variables that can't be shelved (or are ignored) are added to the 
``unshelved`` attribute of the entry.

.. code-block:: python

    from otter.logs import LogEntry
    entry = LogEntry()
    entry.shelve(globals())

The ``shelve`` method also optionally takes a parameter ``variables`` that is a dictionary mapping 
variable names to fully-qualified type strings. If passed, only variables whose names are keys in 
this dictionary and whose types match their corresponding values will be stored in the environment. 
This helps from serializing unnecessary objects and prevents students from injecting malicious code 
into the autograder. To get the type string, use the function ``otter.utils.get_variable_type``. As 
an example, the type string for a pandas ``DataFrame`` is ``"pandas.core.frame.DataFrame"``:

.. code-block:: python

    >>> import pandas as pd
    >>> from otter.utils import get_variable_type
    >>> df = pd.DataFrame()
    >>> get_variable_type(df)
    'pandas.core.frame.DataFrame'

With this, we can tell the log entry to only shelve dataframes named ``df``:

.. code-block:: python

    from otter.logs import LogEntry
    variables = {"df": "pandas.core.frame.DataFrame"}
    entry = LogEntry()
    entry.shelve(globals(), variables=variables)

If you are grading from the log and are utilizing ``variables``, you **must** include this 
dictionary as a JSON string in your configuration, otherwise the autograder will deserialize 
anything that the student submits. This configuration is set in two places: in the :ref:`Otter 
configuration file <otter_check_dot_otter_files>` that you distribute with your notebook and in 
the autograder. Both of these are handled for you if you use :ref:`Otter Assign <otter_assign>` 
to generate your distribution files.

To retrieve a shelved environment from an entry, use the ``LogEntry.unshelve`` method. During the 
process of unshelving, all functions have their ``__globals__`` updated to include everything in the 
unshelved environment and, optionally, anything in the environment passed to ``global_env``.

.. code-block:: python

    >>> env = entry.unshelve() # this will have everything in the shelf in it -- but not factorial
    >>> from math import factorial
    >>> env_with_factorial = entry.unshelve({"factorial": factorial}) # add factorial to all fn __globals__
    >>> "factorial" in env_with_factorial["some_fn"].__globals__
    True
    >>> factorial is env_with_factorial["some_fn"].__globals__["factorial"]
    True

See the reference :ref:`below <logging_otter_logs_reference>` for more information about the 
arguments to ``LogEntry.shelve`` and ``LogEntry.unshelve``.


Debugging with the Log
----------------------

The log is useful to help students debug tests that they are repeatedly failing. Log entries store 
any errors thrown by the process tracked by that entry and, if the log is a call to 
``otter.Notebook.check``, also the test results. Any errors held by the log entry can be re-thrown 
by calling ``LogEntry.raise_error``:

.. code-block:: python

    from otter.logs import Log
    log = Log.from_file(".OTTER_LOG")
    entry = log.entries[0]
    entry.raise_error()

The test results of an entry can be returned using ``LogEntry.get_results``:

.. code-block:: python

    entry.get_results()


Grading from the Log
--------------------

As noted earlier, the environments stored in logs can be used to grade students' assignments. If the 
grading environment does not have the dependencies necessary to run all code, the environment saved 
in the log entries will be used to run tests against. For example, if the execution hub has access 
to a large SQL server that cannot be accessed by a Gradescope grading container, these questions can 
still be graded using the log of checks run by the students and the environments pickled therein.

To configure these pregraded questions, include an :ref:`Otter configuration file 
<otter_check_dot_otter_files>` in the assignment directory that defines the notebook name and 
that the saving of environments should be turned on:

.. code-block:: json

    {
        "notebook": "hw00.ipynb",
        "save_environment": true
    }

If you are restricting the variables serialized during checks, also set the ``variables`` or 
``ignore_modules`` parameters. If you are grading on Gradescope, you must also tell the autograder 
to grade from the log using the ``--grade-from-log`` flag when running or the ``grade_from_log`` 
subkey of ``generate`` if using Otter Assign.


.. _logging_otter_logs_reference:

Otter Logs Reference
--------------------


``otter.logs.Log``
++++++++++++++++++

.. autoclass:: otter.logs.Log
    :members:


``otter.logs.LogEntry``
+++++++++++++++++++++++

.. autoclass:: otter.logs.LogEntry
    :members:


``otter.logs.EventType``
++++++++++++++++++++++++

.. autoclass:: otter.logs.EventType
    :members:
