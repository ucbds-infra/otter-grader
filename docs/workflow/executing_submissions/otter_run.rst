.. _workflow_executing_submissions_otter_run:

Non-containerized Grading
=========================

Otter supports programmatic or command-line grading of assignments without requiring the use of 
Docker as an intermediary. This functionality is designed to allow Otter to run in environments that 
do not support containerization, such as on a user's JupyterHub account. **If Docker is available, 
it is recommended that Otter Grade is used instead, as non-containerized grading is less secure.**

To grade locally, Otter exposes the ``otter run`` command for the command line or the module 
``otter.api`` for running Otter programmatically. The use of both is described in this section. 
Before using Otter Run, you should have generated an :ref:`autograder configuration zip file 
<workflow_otter_generate>`.

Otter Run works by creating a temporary grading directory using the ``tempfile`` library and 
replicating the autograder tree structure in that folder. It then runs the autograder there as 
normal. Note that Otter Run does not run environment setup files (e.g. ``setup.sh``) or install 
requirements, so any requirements should be available in the environment being used for grading.


Grading from the Command Line
-----------------------------

To grade a single submission from the command line, use the ``otter run`` utility. This has one 
required argument, the path to the submission to be graded, and will run Otter in a separate 
directory structure created using ``tempfile``. Use the optional ``-a`` flag to specify a path to 
your configuration zip file if it is not at the default path ``./autograder.zip``. Otter Run will 
write a JSON file, the results of grading, at ``{output_path}/results.json`` (``output_path`` 
can be configured with the ``-o`` flag, and defaults to ``./``).

If I wanted to use Otter Run on ``hw00.ipynb``, I would run

.. code-block::

    otter run hw00.ipynb

If my autograder configuration file was at ``../autograder.zip``, I would run

.. code-block::

    otter run -a ../autograder.zip hw00.ipynb

Either of the above will produce the results file at ``./results.json``. 

For more information on the command-line interface for Otter Run, see the :ref:`cli_reference`.


Grading Programmatically
------------------------

Otter includes an API through which users can grade assignments from inside a Python session, 
encapsulated in the submodule ``otter.api``. The main method of the API is 
``otter.api.grade_submission``, which takes in an autograder configuration file path and a 
submission path and grades the submission, returning the ``GradingResults`` object that was produced 
during grading.

For example, to grade ``hw00.ipynb`` with an autograder configuration file in ``autograder.zip``, I 
would run

.. code-block:: python

    from otter.api import grade_submission
    grade_submission("hw00.ipynb", "autograder.zip")

``grade_submission`` has an optional argument ``quiet`` which will suppress anything printed to the 
console by the grading process during execution when set to ``True`` (default ``False``).

For more information about grading programmatically, see the :ref:`API reference <api_reference>`.


Grading Results
+++++++++++++++

This section describes the object that Otter uses to store and manage test case scores when grading. 

.. autoclass:: otter.test_files.GradingResults
    :members:
