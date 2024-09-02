.. _home:

Otter-Grader Documentation
==========================

.. toctree::
    :maxdepth: 1
    :hidden:

    tutorial
    test_files/index
    otter_assign/index
    otter_check/index
    workflow/index
    execution
    debugging
    plugins/index
    pdfs
    seeding
    logging
    api_reference
    cli_reference
    resources
    Changelog <https://github.com/ucbds-infra/otter-grader/tree/master/CHANGELOG.md>

Otter Grader is a light-weight, modular open-source autograder developed by the Data Science 
Education Program at UC Berkeley. It is designed to grade Python and R assignments for classes at 
any scale by abstracting away the autograding internals in a way that is compatible with any 
instructor's assignment distribution and collection pipeline. Otter supports local grading through 
parallel Docker containers, grading using the autograding platforms of 3rd-party learning management 
systems (LMSs), non-containerized grading on an instructor's machine, and a client package 
that allows students to check and instructors to grade assignments their own machines. Otter is 
designed to grade Python and R executables, Jupyter Notebooks, and RMarkdown documents and is 
compatible with a few different LMSs, including Canvas and Gradescope.

The core abstraction of Otter, as compared to other autograders like nbgrader_ and OkPy_, is this:
you provide the compute, and Otter takes care of the rest. All a instructor needs to do in order to 
autograde is find a place to run Otter (a server, a JupyterHub, their laptop, etc.) and Otter will
take care of generating assignments and tests, creating and managing grading environents, and 
grading submissions. Otter is platform-agnostic, allowing you to put and grade your assignments 
anywhere you want.

.. _nbgrader: https://nbgrader.readthedocs.io/en/stable/
.. _OkPy: https://okpy.org/

Otter is organized into six components based on the different stages of the assignment pipeline, 
each with a command-line interface:

* :ref:`Otter Assign <otter_assign>` is an assignment development and distribution tool that 
  allows instructors to create assignments with prompts, solutions, and tests in a simple notebook 
  format that it then converts into santized versions for distribution to students and autograders.
* :ref:`Otter Generate <workflow_otter_generate>` creates the necessary setup files so that 
  instructors can autograde assignments.
* :ref:`Otter Check <otter_check>` allows students to run publically distributed tests written 
  by instructors against their solutions as they work through assignments to verify their thought 
  processes and implementations.
* :ref:`Otter Export <pdfs>` generates PDFs with optional filtering of Jupyter Notebooks for manually 
  grading portions of assignments.
* :ref:`Otter Run <workflow_executing_submissions_otter_run>` grades students' assignments locally on 
  the instructor's machine without containerization and supports grading on a JupyterHub account.
* :ref:`Otter Grade <workflow_executing_submissions_otter_grade>` grades students' assignments 
  locally on the instructor's machine in parallel Docker containers, returning grade breakdowns as a 
  CSV file.


.. _installation:

Installation
------------

Otter is a Python package that is compatible with Python 3.9+. The PDF export internals require 
either LaTeX and Pandoc or Playwright and Chromium to be installed. Docker is also required to grade
assignments locally with containerization. Otter's Python package can be installed using pipx_ or pip.

.. _pipx: https://pipx.pypa.io/

.. code-block:: console

    pipx install otter-grader

    # or
    pip install otter-grader

Installing the Python package will install the ``otter`` binary so that Otter can be called from the 
command line. If you installed with pip, you can also call Otter as a Python module with
``python3 -m otter``.

If you are going to be autograding R, you must also install the R package ``ottr``:

.. code-block:: r

    install.packages("ottr")
