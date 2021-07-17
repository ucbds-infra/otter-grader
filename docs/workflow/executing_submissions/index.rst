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
