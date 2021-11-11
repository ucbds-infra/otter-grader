Tutorial
========

This tutorial can help you to verify that you have installed Otter correctly and introduce you to 
the general Otter workflow. Once you have :ref:`installed <home>` Otter, download `this zip file 
<_static/tutorial.zip>`_ and unzip it into some directory on your machine; you should have the 
following directory structure:

.. code-block::

    tutorial
    ├── demo.ipynb
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

This section describes the basic execution of Otter's tools using the provided zip file. It is meant 
to verify your installation and to *loosely* describe how a few Otter tools are used. This tutorial 
covers Otter Assign, Otter Generate, and Otter Grade.


Otter Assign
------------

Start by moving into the ``tutorial`` directrory. This directory includes the master notebook 
``demo.ipynb``. Look over this notebook to get an idea of its structure. It contains five questions, 
four code and one Markdown (two of which are manually-graded). Also note that the assignment 
configuration in the first cell tells Otter Assign to generate a solutions PDF and an 
autograder zip file and to include special submission instructions before the export cell. To run 
Otter Assign on this notebook, run

.. code-block:: console

    $ otter assign demo.ipynb dist --v1
    Generating views...
    Generating solutions PDF...
    Generating autograder zipfile...
    Running tests...
    All tests passed!

The use of the ``--v1`` flag indicates that this is an :ref:`Otter Assign format v1 formatted 
notebook <otter_assign>`.

Otter Assign should create a ``dist`` directory which contains two further subdirectories: 
``autograder`` and ``student``. The ``autograder`` directory contains the Gradescope autograder, 
solutions PDF, and the notebook with solutions. The ``student`` directory contains just the 
sanitized student notebook.

.. code-block::

    tutorial/dist
    ├── autograder
    │   ├── autograder.zip
    │   ├── demo-sol.pdf
    │   ├── demo.ipynb
    │   ├── otter_config.json
    │   └── requirements.txt
    └── student
        └── demo.ipynb

For more information about the configurations for Otter Assign and its output format, see 
:reF:`otter_assign`.


Otter Generate
--------------

In the ``dist/autograder`` directory created by Otter Assign, there should be a file called 
``autograder.zip``. This file is the result of using Otter Generate to generate a zip file with all 
of your tests and requirements, which is done invisibly by Otter Assign when it is used (which it is 
configured to do in the assignment metadata). Alternatively, you could generate this zip file 
yourself from the contents of ``dist/autograder`` by running

.. code-block:: console

    otter generate

in that directory (but this is not recommended).


Otter Grade
-----------

**Note:** You should complete the Otter Assign tutorial above before running this tutorial, as you 
will need some of its output files.

At this step of grading, the instructor faces a choice: where to grade assignments. The rest of this 
tutorial details how to grade assignments locally using Docker containers on the instructor's 
machine. You can also grade on Gradescope or without containerization, as described in the 
:ref:`workflow_executing_submissions` section.

Let's now construct a call to Otter that will grade these notebooks. We will use 
``dist/autograder/autograder.zip`` from running Otter Assign to configure our grading image. Our notebooks 
are in the ``ipynbs`` subdirectory, so we'll need to use the ``-p`` flag. The notebooks also contain 
a couple of written questions, and the :ref:`filtering <pdfs>` is implemented using HTML comments, so 
we'll specify the ``--pdfs`` flag to indicate that Otter should grab the PDFs out of the Docker 
containers.

Let's run Otter on the notebooks:

.. code-block:: console

    otter grade -p submissions/ipynbs -a dist/autograder/demo-autograder_*.zip --pdfs -v

(The ``-v`` flag so that we get verbose output.) After this finishes running, there 
should be a new file and a new folder in the working directory: ``final_grades.csv`` and 
``submission_pdfs``. The former should contain the grades for each file, and should look something 
like this:

.. code-block::

    file,q1,q2,q3
    fails3Hidden.ipynb,1.0,1.0,0.5
    passesAll.ipynb,1.0,1.0,1.0
    fails1.ipynb,0.6666666666666666,1.0,1.0
    fails2Hidden.ipynb,1.0,0.5,1.0
    fails3.ipynb,1.0,1.0,0.375
    fails2.ipynb,1.0,0.0,1.0

Let's make that a bit prettier:

.. list-table::
    :header-rows: 1

    * - file
      - q1
      - q2
      - q3
    * - fails3Hidden.ipynb
      - 1.0
      - 1.0
      - 0.5
    * - passesAll.ipynb
      - 1.0
      - 1.0
      - 1.0
    * - fails1.ipynb
      - 0.6666666666666666
      - 1.0
      - 1.0
    * - fails2Hidden.ipynb
      - 1.0
      - 0.5
      - 1.0
    * - fails3.ipynb
      - 1.0
      - 1.0
      - 0.375
    * - fails2.ipynb
      - 1.0
      - 0.0
      - 1.0


The latter, the ``submission_pdfs`` directory, should contain the filtered PDFs of each notebook 
(which should be relatively similar).

Otter Grade can also grade the zip file exports provided by the ``Notebook.export`` method. Before 
grading the zip files, you must edit your ``autograder.zip`` to incdicate that you're doing so. To 
do this, open ``demo.ipynb`` (the file we used with Otter Assign) and edit the first cell of the 
notebook (beginning with ``BEGIN ASSIGNMENT``) so that the ``zips`` key under ``generate`` is 
``true`` in the YAML and rerun Otter Assign.

Now, all we need to do is add the ``-z`` flag to the call to indicate that you're grading these zip 
files. We have provided some, with the same notebooks as above, in the ``zips`` directory, so let's 
grade those:

.. code-block:: console

    otter grade -p submissions/zips -a dist/autograder/demo-autograder_*.zip -vz

This should have the same CSV output as above but no ``submission_pdfs`` directory since we didn't 
tell Otter to generate PDFs.

You can learn more about the grading workflow for Otter in :ref:`this section <workflow>`.
