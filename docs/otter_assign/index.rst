.. _otter_assign:

Creating Assignments
====================

.. 
    The documentation for Otter Assign is forked from the docs for jassign: 
    https://github.com/okpy/jassign/blob/master/docs/notebook-format.md

.. toctree::
   :maxdepth: 1
   :hidden:

   v0/index
   v1/index

Otter ships with an assignment development and distribution tool called Otter Assign, an 
Otter-compliant fork of `jAssign <https://github.com/okpy/jassign>`_ that was designed for OkPy. 
Otter Assign allows instructors to create assignments by writing questions, prompts, solutions, and 
public and private tests all in a single notebook, which is then parsed and broken down into student 
and autograder versions.

Otter Assign currently supports two notebook formats: format v0, the original master notebook format,
and format v1, which was released with Otter-Grader v3. Format v0 is currently the default format
option but v1 will become the default in Otter-Grader v4.

To run Otter Assign on a v1-formatted notebook, add the ``--v1`` flag to the command:

.. code-block:: console

    otter assign lab00.ipynb dist --v1
