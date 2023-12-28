.. _workflow_executing_submissions_otter_grade:

Grading Locally
===============

The command line interface allows instructors to grade notebooks locally by launching Docker 
containers on the instructor's machine that grade notebooks and return a CSV of grades and 
(optionally) PDF versions of student submissions for manually graded questions.


A Note on Docker
----------------

In previous versions of Otter (pre-v5), Otter had its own Docker image called
``ucbdsinfra/otter-grader`` which was required to be used as the base image for the containers that
Otter used to grade assignments. That image has since been removed, and instead Otter relies on the
same scripts it uses to set up its grading image on Gradescope to set up container images for local
grading. The new default image for local grading is ``ubuntu:22.04``, and all dependencies are
re-downloaded when the image for an assignment is built for the first time.


Assignment Names
++++++++++++++++

Whenever you use Otter Grade, you must specify an assignment name with the ``-n`` or ``--name``
flag. This assignment name is used as the tag for the Docker image that Otter creates (so you will
have an image called ``otter-grade:{assignment name}`` for each assignment). These assignment names
are required so that Otter can make effective user of Docker's image layer cache. This means that if
you make changes to tests or need to grade an assignment twice, Docker doesn't need to reinstall all
of the dependencies Otter defines.

These images can be quite large (~4GB), so Otter provides a way to easily prune all of the Docker
images it has created:

.. code-block:: console

    otter grade --prune

This will prompt you to confirm that you would like to delete all of the images, which cannot be
undone. After doing this, there may be some layers still in Docker's image cache (this command only
deletes images with the ``otter-grade`` name), so if you need to free up space, you can delete these
dangling images with ``docker image prune``.


Configuration Files
-------------------

Otter grades students submissions in individual Docker containers that are based on a Docker image 
generated through the use of a configuration zip file. Before grading assignments locally, an 
instructor should create such a zip file by using a tool such as :ref:`Otter Assign 
<otter_assign>` or :ref:`Otter Generate <workflow_otter_generate>`.


Using the CLI
-------------

Before using the command line utility, you should have

* written tests for the assignment, 
* generated a configuration zip file from those tests, and
* downloaded submissions

The grading interface, encapsulated in the ``otter grade`` command, runs the local grading process 
and defines the options that instructors can set when grading. A comprehensive list of flags is 
provided in the :ref:`cli_reference`.


Basic Usage
+++++++++++

The simplest usage of the Otter Grade is when we have a directory structure as below (and we have 
changed directories into ``grading`` in the command line) and we don't require PDFs or additional 
requirements.

.. code-block::

    grading
    ├── autograder.zip
    ├── nb0.ipynb
    ├── nb1.ipynb
    ├── nb2.ipynb  # etc.
    └── tests
        ├── q1.py
        ├── q2.py
        └── q3.py  # etc.

Otter Grade has only one required flag, the ``-n`` flag for the assignment name (which we'll call
``hw01``), so in the case above, our otter command is very simple:

.. code-block:: console

    otter grade -n hw01 *.ipynb

Because our configuration file is at ``./autograder.zip``, and we don't mind output to ``./``, we
can use the defualt values of the ``-a`` and ``-o`` flags. This leaves only ``-n`` and the
submission paths as the required arguments.

Note that the submission path(s) can also be specified as directories, in which case the ``--ext``
flag is used to determine the extension of the submission files (which defaults to ``ipynb``).
Therefore, the following command is equivalent to the one above in this scenario:

.. code-block:: console

    otter grade -n hw01 .

After grader, our directory will look like this:

.. code-block::

    grading
    ├── autograder.zip
    ├── final_grades.csv
    ├── nb0.ipynb
    ├── nb1.ipynb
    ├── nb2.ipynb  # etc.
    └── tests
        ├── q1.py
        ├── q2.py
        └── q3.py  # etc.

and the grades for each submission will be in ``final_grades.csv``.

If we wanted to generate PDFs for manual grading, we wouldadd the ``--pdfs`` flag to tell Otter to
copy the PDFs out of the containers: 

.. code-block::

    otter grade -n hw01 --pdfs .

and at the end of grading we would have

.. code-block::

    grading
    ├── autograder.zip
    ├── final_grades.csv
    ├── nb0.ipynb
    ├── nb1.ipynb
    ├── nb2.ipynb    # etc.
    ├── submission_pdfs
    │   ├── nb0.pdf
    │   ├── nb1.pdf
    │   └── nb2.pdf  # etc.
    └── tests
        ├── q1.py
        ├── q2.py
        └── q3.py    # etc.

When a single file path is passed to ``otter grade``, the submission score as a percentage is
returned to the command line as well.

.. code-block:: console

    otter grade -n hw01 ./nb0.ipynb

To grade submissions that aren't notebook files, use the ``--ext`` flag, which accepts the file 
extension to search for submissions with. For example, if we had the same example as above but with 
Rmd files:

.. code-block:: console

    otter grade --ext Rmd .

If you're grading submission export zip files (those generated by ``otter.Notebook.export`` or 
``ottr::export``), you should pass ``--ext zip`` to ``otter grade``.

.. code-block:: console

    otter grade --ext zip .
