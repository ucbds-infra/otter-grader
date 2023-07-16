.. _workflow_executing_submissions:

Executing Submissions
=====================

.. toctree::
    :maxdepth: 1
    :hidden:

    otter_grade
    gradescope
    otter_run

This section describes how students' submissions can be executed using the configuration file from 
:ref:`the previous part <workflow_otter_generate>`. There are three main options for executing 
students' submissions:

* **local grading**, in which the assignments are downloaded onto the instructor's machine and 
  graded in parallelized Docker containers,
* **Gradescope**, in which the zip file is uploaded to a Programming Assignment and students 
  submit to the Gradescope web interface, or
* **non-containerized local grading**, in which assignments are graded in a temporary directory 
  structure on the user's machine

The first two options are recommended as they provide better security by sandboxing students' 
submissions in containerized environments. The third option is present for users who are running on 
environments that don't have access to Docker (e.g. running on a JupyterHub account).


Execution
---------

All of the options listed above go about autograding the submission in the same way; this section
describes the steps taken by the autograder to generate a grade for the student's autogradable
work.

The steps taken by the autograder are:

#. Copies the tests and support files from the autograder source (the contents of the autograder
   configuration zip file)
#. Globs all ``.ipynb`` files in the submission directory and ensures there are >= 1, taking that
   file as the submission
#. Reads in the log from the submission if it exists
#. Executes the notebook using the tests provided in the autograder source (or the log if indicated)
#. Looks for discrepancies between the logged scores and the public test scores and warns about 
   these if present
#. If indicated, exports the notebook as a PDF and submits this PDF to the PDF Gradescope assignment
#. Makes adjustments to the scores and visibility based on the configurations
#. Generates a Gradescope-formatted JSON file for results and serializes the results object to a
   pickle file
#. Prints the results as a dataframe to stdout


.. _workflow_execution_submissions_assignment_name_verification:

Assignment Name Verification
++++++++++++++++++++++++++++

To ensure that students have uploaded submissions to the correct assignment on your LMS, you can
configure Otter to check for an assignment name in the notebook metadata of the submission. If you
set the ``assignment_name`` key of your ``otter_config.json`` to a string, Otter will check that the
submission has this name as ``nb["metadata"]["otter"]["assignment_name"]`` (or, in the case of R
Markdown submissions, the ``assignment_name`` key of the YAML header) before grading it. (This
metadata can be set automatically with Otter Assign.) If the name doesn't match or there is no name,
an error will be raised and the assignment will not be graded. If the ``assignment_name`` key is not
present in your ``otter_config.json``, this validation is turned off.
