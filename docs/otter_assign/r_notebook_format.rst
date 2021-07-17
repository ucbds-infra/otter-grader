R Notebook Format
=================

Otter Assign is compatible with Otter's R autograding system and currently supports Jupyter notebook 
master documents. The format for using Otter Assign with R is very similar to the Python format with 
a few important differences.


Assignment Metadata
-------------------

As with Python, Otter Assign for R also allows you to specify various assignment generation 
arguments in an assignment metadata cell.

.. code-block:: markdown

    ```
    BEGIN ASSIGNMENT
    init_cell: false
    export_cell: true
    ...
    ```

This cell is removed from both output notebooks. Any unspecified keys will keep their default 
values. For more information about many of these arguments, see :ref:`otter_assign_usage`. The YAML 
block below lists all configurations **supported with R** and their 
defaults. Any keys that appear in the Python section but not below will be ignored when using Otter 
Assign with R.

.. code-block:: yaml

    requirements: requirements.txt # path to a requirements file for Gradescope; appended by default
    overwrite_requirements: false  # whether to overwrite Otter's default requirements rather than appending
    environment: environment.yml   # path to custom conda environment file
    template_pdf: false            # whether to generate a manual question template PDF for Gradescope
    generate:                      # configurations for running Otter Generate; defaults to false
        points: null                 # number of points to scale assignment to on Gradescope
        threshold: null              # a pass/fail threshold for the assignment on Gradescope
        show_stdout: false           # whether to show grading stdout to students once grades are published
        show_hidden: false           # whether to show hidden test results to students once grades are published
    files: []                      # a list of file paths to include in the distribution directories


Autograded Questions
--------------------

Here is an example question in an Otter Assign for R formatted notebook:

.. image:: images/R_assign_sample_question.png
    :target: images/R_assign_sample_question.png
    :alt: 

For code questions, a question is a description *Markdown* cell, followed by a solution *code* cell 
and zero or more test *code* cells. The description cell must contain a code block (enclosed in 
triple backticks ```````) that begins with ``BEGIN QUESTION`` on its own line, followed by YAML that 
defines metadata associated with the question.

The rest of the code block within the description cell must be YAML-formatted with the following 
fields (in any order):

* ``name`` (required) - a string identifier that is a legal file name (without an extension)
* ``manual`` (optional) - a boolean (default ``false``); whether to include the response cell in a 
  PDF for manual grading
* ``points`` (optional) - a number or list of numbers for the point values of each question. If a 
  list of values, each case gets its corresponding value. If a single value, the number is divided 
  by the number of cases so that a question with :math:`n` cases has test cases worth 
  :math:`\frac{\text{points}}{n}` points.

As an example, the question metadata below indicates an autograded question ``q1`` with 3 subparts 
worth 1, 2, and 1 points, respectively.

.. code-block:: markdown

    ```
    BEGIN QUESTION
    name: q1
    points: 
        - 1
        - 2
        - 1
    ```


Solution Removal
++++++++++++++++

Solution cells contain code formatted in such a way that the assign parser replaces lines or 
portions of lines with prespecified prompts. The format for solution cells in R notebooks is the 
same as in Python notebooks, described :ref:`here <otter_assign_python_solution_removal>`. Otter Assign's 
solution removal for prompts is compatible with normal strings in R, including assigning these to a 
dummy variable so that there is no undesired output below the cell:

.. code-block:: r

    # this is OK:
    . = " # BEGIN PROMPT
    some.var <- ...
    " # END PROMPT


Test Cells
++++++++++

The test cells are any code cells following the solution cell that begin with the comment 
``## Test ##`` or ``## Hidden Test ##`` (case insensitive). A ``Test`` is distributed to students 
so that they can validate their work. A ``Hidden Test`` is not distributed to students, but is used 
for scoring their work. When writing tests, each test cell should be a single call to 
``testthat::test_that`` and there should be no code outside of the ``test_that`` call. For 
example, instead of

.. code-block:: r

    ## Test ##
    data = data.frame()
    test_that("q1a", {
        # some test
    })

do the following:

.. code-block:: r

    ## Test ##
    test_that("q1a", {
        data = data.frame()
        # some test
    })

The removal behavior regarding questions with no solution provided holds for R notebooks.

Manually Graded Questions
-------------------------

Otter Assign also supports manually-graded questions using a similar specification to the one 
described above. The behavior for manually graded questions in R is exactly the same as it is in 
:ref:`Python <otter_assign_python_manual_questions>`.
