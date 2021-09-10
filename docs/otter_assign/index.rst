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

.. code-block:: console

    otter assign lab00.ipynb dist


Converting to v1
----------------

Otter includes a tool that will help you convert a v0-formatted notebook to v1 format. To convert
a notebook, use the module ``otter.assign.v0.convert`` from the Python CLI. This tool takes two
position arguments: the path to the original notebook and the path at which to write the new
notebook. For example,

.. code-block:: console

    python3 -m otter.assign.v0.convert lab01.ipynb lab01-v1.ipynb
