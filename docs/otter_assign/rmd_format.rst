R Markdown Format
=================

Otter Assign is compatible with Otter's R autograding system and currently supports Jupyter notebook 
and R Markdown master documents. The format for using Otter Assign with R is very similar to the 
Python format with a few important differences. The main difference is that, where in the notebook
format you would use raw cells, in R Markdown files you wrap what would normally be in a raw cell in
an HTML comment.

For example, a ``# BEGIN TESTS`` cell in R Markdown looks like:

.. code-block:: markdown

    <!-- # BEGIN TESTS -->

For cells that contain YAML configurations, you can use a multiline comment:

.. code-block:: markdown

    <!--
    # BEGIN QUESTION
    name: q1
    -->


Assignment Config
-----------------

As with Python, Otter Assign for R Markdown also allows you to specify various assignment generation 
arguments in an assignment config comment:

.. code-block:: markdown

    <!--
    # ASSIGNMENT CONFIG
    init_cell: false
    export_cell: true
    generate: true
    # etc.
    -->

You can find a list of available metadata keys and their defaults in the :ref:`notebook format 
section <otter_assign_assignment_metadata>`.


Autograded Questions
--------------------

Here is an example question in an Otter Assign-formatted R Markdown question:

.. code-block:: markdown

    <!--
    # BEGIN QUESTION
    name: q1
    manual: false
    points:
        - 1
        - 1
    -->

    **Question 1:** Find the radius of a circle that has a 90 deg. arc of length 2. Assign this 
    value to `ans.1`

    <!-- # BEGIN SOLUTION -->

    ```{r}
    ans.1 <- 2 * 2 * pi * 2 / pi / pi / 2 # SOLUTION
    ```

    <!-- # END SOLUTION -->

    <!-- # BEGIN TESTS -->

    ```{r}
    expect_true(ans.1 > 1)
    expect_true(ans.1 < 2)
    ```

    ```{r}
    # HIDDEN
    tol = 1e-5
    actual_answer = 1.27324
    expect_true(ans.1 > actual_answer - tol)
    expect_true(ans.1 < actual_answer + tol)
    ```

    <!-- # END TESTS -->

    <!-- # END QUESTION -->

For code questions, a question is a some description markup, followed by a solution code blocks and 
zero or more test code blocks. The blocks should be wrapped in HTML comments following the same
structure as the notebook autograded question. The question config has the same keys as the notebook
question config.

As an example, the question config below indicates an autograded question ``q1`` with 3 subparts
worth 1, 2, and 1 points, resp.

.. code-block:: markdown

    <!--
    # BEGIN QUESTION
    name: q1
    points: 
        - 1
        - 2
        - 1
    -->


Solution Removal
++++++++++++++++

Solution cells contain code formatted in such a way that the assign parser replaces lines or 
portions of lines with pre-specified prompts. The format for solution cells in Rmd files is the same 
as in Python and R Jupyter notebooks, described :ref:`here <otter_assign_python_solution_removal>`. 
Otter Assign's solution removal for prompts is compatible with normal strings in R, including 
assigning these to a dummy variable so that there is no undesired output below the cell:

.. code-block:: r

    # this is OK:
    . = " # BEGIN PROMPT
    some.var <- ...
    " # END PROMPT


Test Cells
++++++++++

Any cells within the ``# BEGIN TESTS`` and ``# END TESTS`` boundary cells are considered test cells.
There are two types of tests: public and hidden tests.
Tests are public by default but can be hidden by adding the ``# HIDDEN`` comment as the first line
of the cell. A hidden test is not distributed to students, but is used for scoring their work.

When writing tests, each test cell maps to a single test case and should
raise an error if the test fails. The removal behavior regarding questions with no solution 
provided holds for R Markdown files.

.. code-block:: r

    testthat::expect_true(some_bool)

.. code-block:: r

    testthat::expect_equal(some_value, 1.04)

As with notebooks, test cells also support test config blocks; for more information on these, see
:ref:`otter_assign_r_test_cells`.


Manually-Graded Questions
-------------------------

Otter Assign also supports manually-graded questions using a similar specification to the one 
described above. To indicate a manually-graded question, set ``manual: true`` in the question 
config. A manually-graded question is defined by three parts:

* a question config
* (optionally) a prompt
* a solution

Manually-graded solution cells have two formats:

* If the response is code (e.g. making a plot), they can be delimited by solution removal syntax as
  above.
* If the response is markup, the the solution should be wrapped in special HTML comments (see below) 
  to indicate removal in the sanitized version.

To delimit a markup solution to a manual question, wrap the solution in the HTML comments 
``<!-- # BEGIN SOLUTION -->`` and ``<!-- # END SOLUTION -->`` on their own lines to indicate that
the content in between should be removed.

.. code-block:: markdown

    <!-- # BEGIN SOLUTION -->

    solution goes here

    <!-- # END SOLUTION -->

To use a custom Markdown prompt, include a ``<!-- # BEGIN/END PROMPT -->`` block with a solution 
block:

.. code-block:: markdown

    <!-- # BEGIN PROMPT -->

    prompt goes here

    <!-- # END PROMPT -->

    <!-- # BEGIN SOLUTION -->

    solution goes here

    <!-- # END SOLUTION -->

If no prompt is provided, Otter Assign automatically replaces the solution with a line 
containing ``_Type your answer here, replacing this text._``.

An example of a manually-graded code question:

.. code-block:: markdown

    <!--
    # BEGIN QUESTION
    name: q7
    manual: true
    -->

    **Question 7:** Plot $f(x) = \cos e^x$ on $[0,10]$.

    <!-- # BEGIN SOLUTION -->

    ```{r}
    # BEGIN SOLUTION
    x = seq(0, 10, 0.01)
    y = cos(exp(x))
    ggplot(data.frame(x, y), aes(x=x, y=y)) +
        geom_line()
    # END SOLUTION
    ```

    <!-- # END SOLUTION -->

    <!-- # END QUESTION -->

An example of a manually-graded written question (with no prompt):

.. code-block:: markdown

    <!--
    # BEGIN QUESTION
    name: q5
    manual: true
    -->

    **Question 5:** Simplify $\sum_{i=1}^n n$.

    <!-- # BEGIN SOLUTION -->

    $\frac{n(n+1)}{2}$

    <!-- # END SOLUTION -->

    <!-- # END QUESTION -->

An example of a manually-graded written question with a custom prompt:

.. code-block:: markdown

    <!--
    # BEGIN QUESTION
    name: q6
    manual: true
    -->

    **Question 6:** Fill in the blank.

    <!-- # BEGIN PROMPT -->

    The mitochondria is the ___________ of the cell.

    <!-- # END PROMPT -->

    <!-- # BEGIN SOLUTION-->

    powerhouse

    <!-- # END SOLUTION -->

    <!-- # END QUESTION -->
