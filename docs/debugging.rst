Debugging Submissions
=====================

To help debug submissions that are not passing tests or which are behaving oddly, it can be helpful
to use Otter's debug mode. The main use for debug mode is to examine errors that are being thrown
in the submission and which Otter swallows during normal execution. This is a guide for setting up
an environment where Otter's debug mode is enabled and for using it.


Setting Up a Debugging Environment
----------------------------------

The first step is to set up a debugging environment. This step depends on how you're executing the
submissions. If you're using containerized local grading (``otter grade``) or Gradescope, follow the
steps in this section. If you're using non-containerized grading (``otter run``), follow the steps
in :ref:`debugging_with_otter_run`.


Otter Grade Setup
+++++++++++++++++

To create a container for debugging a submission, use the Docker image that was created for your
assignment when you ran ``otter grade``. The image's tag will use the assignment name (the value of
the ``-n`` or ``--name`` flag). If you passed ``-n hw01``, the image name will be
``otter-grade:hw01``. Create a container using this image and run bash:

.. code-block:: console

    docker run -it otter-grade:<assignment name> bash

This should create the container and drop you into a bash prompt inside of it. Now, in a separate
terminal, copy the submission file into the container you've just created:

.. code-block:: console

    docker cp path/to/subm.ipynb <container id>:/autograder/submission/subm.ipynb

You can get the container ID either from the prompt in the container's bash shell or from the
``docker container ls`` command.

Now that you've set up the grading environment, continue with the debugging steps
:ref:`below <debugging_container>`. Once you're finished debugging, remember to stop the container
and remove it.


Gradescope Setup
++++++++++++++++

Find the submission you would like to debug on Gradescope and use Gradescope's `Debug via SSH
feature <https://gradescope-autograders.readthedocs.io/en/latest/ssh/>`_ to create a container with
that submission and SSH into it, then continue with the debugging steps
:ref:`below <debugging_container>`.


.. _debugging_container:

Debugging in a Container
------------------------

In the container, ``cd`` into the ``/autograder/source`` directory. There should be an
``otter_config.json`` file in this directory containing Otter's autograder configuration. (If there
isn't one present, make one.) Edit this file to set ``"debug"`` to ``true`` (this enables debug
mode).

Now ``cd`` into ``/autograder`` and run

.. code-block:: console

    ./run_autograder

This shell script runs Otter and its results should be printed to the console. If an error is thrown
while executing the notebook, it will be shown and the autograder will stop. If you're running on
Gradescope, no changes or autograder runs made here will affect the submission or its grade.

If you need to edit the submission file(s), they are located in the ``/autograder/submission``
directory.


Viewing the Executed Notebook
+++++++++++++++++++++++++++++

To view the notebook with its outputs from grading, you can copy the ``results.pkl`` file out from
the container and extract the notebook from it. On Gradescope, you would use SFTP to connect to the
container while it's still running and download the file ``/autograder/results/results.pkl``. For
local grading, run

.. code-block:: console

    docker cp <container id>:/autograder/results/results.pkl results.pkl

to copy the file out of the container.

Once you have obtained the ``results.pkl`` file, run this Python snippet to copy the notebook out of
it.

.. code-block:: python

    import dill
    import nbformat

    with open("results.pkl", "rb") as f:
        res = dill.load(f)

    nbformat.write(res.notebook, "executed.ipynb")


.. _debugging_with_otter_run:

Debugging with Otter Run
------------------------

Read the :ref:`previous section <debugging_container>` first. Because Otter Run relies on an
autograder zip file for its configuration intsead of a Docker container, you will need to manually
edit the ``otter_config.json`` file in your autograder zip file to set ``"debug"`` to ``true``.
Then, re-zip the zip file's contents and use this new autograder zip file for ``otter run``.


Viewing the Executed Notebook
+++++++++++++++++++++++++++++

If you want access to the executed notebook when using Otter Run, you will need to call it from
Python instead of using the CLI. Run a script like the one below to grade the submission and obtain
the notebook.

.. code-block:: python

    import nbformat
    from otter.api import grade_submission

    # res is the GradingResults object, so you can examine it to see the score details
    res = grade_submission("submission.ipynb", ag_path="autograder.zip", debug=True)
    nbformat.write(res.notebook, "executed.ipynb")

You can find details about the ``GradingResults`` class
:ref:`here <workflow_executing_submissions_otter_run_grading_results>`.
