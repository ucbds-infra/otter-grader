.. _workflow:

Grading Workflow
================

.. toctree::
    :maxdepth: 1
    :hidden:

    otter_generate/index
    executing_submissions/index

The workflow for grading with Otter is very standard irrespective of the medium by which instructors 
will collect students' submissions. In general, it is a four-step process:

#. Generate a configuration zip file
#. Collect submissions via LMS (Canvas, Gradescope, etc.)
#. Run the autograder on each submission
#. Grade written questions via LMS

Steps 1 and 3 above are covered in this section of the documentation. All Otter autograders require 
a configuration zip file, the creation of which is described in :ref:`the next section 
<workflow_otter_generate>`, and this zip file is used to create a grading environment. There are 
various options for where and how to grade submissions, both containerized and non-containerized, 
described in :ref:`workflow_executing_submissions`.
