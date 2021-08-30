RMarkdown Format
================

Otter Assign is compatible with Otter's R autograding system and currently supports Jupyter notebook 
and RMarkdown master documents. The format for using Otter Assign with R is very similar to the 
Python format with a few important differences.


Assignment Metadata
-------------------

As with Python, Otter Assign for R also allows you to specify various assignment generation 
arguments in an assignment metadata code block.

.. code-block:: markdown

    ```
    BEGIN ASSIGNMENT
    init_cell: false
    export_cell: true
    # etc.
    ```

You can find a list of available metadata keys and their defaults in the :ref:`notebook format 
section <otter_assign_v1_assignment_metadata>`.


Autograded Questions
--------------------

Here is an example question in an Otter Assign-formatted Rmd file:

.. code-block:: markdown

    **Question 1:** Find the radius of a circle that has a 90 deg. arc of length 2. Assign this 
    value to `ans.1`

    ```
    BEGIN QUESTION
    name: q1
    manual: false
    points:
        - 1
        - 1
    ```

    ```{r}
    ans.1 <- 2 * 2 * pi * 2 / pi / pi / 2 # SOLUTION
    ```

    ```{r}
    ## Test ##
    expect_true(ans.1 > 1)
    expect_true(ans.1 < 2)
    ```

    ```{r}
    ## Hidden Test ##
    tol = 1e-5
    actual_answer = 1.27324
    expect_true(ans.1 > actual_answer - tol)
    expect_true(ans.1 < actual_answer + tol)
    ```

For code questions, a question is a some description markup, followed by a solution code blocks and 
zero or more test code blocks. The description must contain a code block (enclosed in triple 
backticks ```````) that begins with ``BEGIN QUESTION`` on its own line, followed by YAML that 
defines metadata associated with the question.

The rest of the code block within the description cell must be YAML-formatted with the following f
ields (in any order):

* ``name`` (required) - a string identifier that is a legal file name (without an extension)
* ``manual`` (optional) - a boolean (default ``false``); whether to include the response cell in a 
  PDF for manual grading
* ``points`` (optional) - a number or list of numbers for the point values of each question. If a 
  list of values, each case gets its corresponding value. If a single value, the number is divided 
  by the number of cases so that a question with :math:`n` cases has test cases worth 
  :math:`\frac{\text{points}}{n}` points.

As an example, the question metadata below indicates an autograded question ``q1`` with 3 subparts
worth 1, 2, and 1 points, resp.

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
portions of lines with prespecified prompts. The format for solution cells in Rmd files is the same 
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

The test cells are any code cells following the solution cell that begin with the comment 
``## Test ##`` or ``## Hidden Test ##`` (case insensitive). A ``Test`` is distributed to students 
so that they can validate their work. A ``Hidden Test`` is not distributed to students, but is used 
for scoring their work. When writing tests, each test cell maps to a single test case and should
raise an error if the test fails. The removal behavior regarding questions with no solution 
provided holds for R notebooks.

.. code-block:: r

    ## Test ##
    testthat::expect_true(some_bool)

.. code-block:: r

    ## Hidden Test ##
    testthat::expect_equal(some_value, 1.04)


Manually Graded Questions
-------------------------

Otter Assign also supports manually-graded questions using a similar specification to the one 
described above. To indicate a manually-graded question, set ``manual: true`` in the question 
metadata. A manually-graded question is defined by three parts:

* a question metadata
* (optionally) a prompt
* a solution

Manually-graded solution cells have two formats:

* If the response is code (e.g. making a plot), they can be delimited by solution removal syntax as
  above.
* If the response is markup, the the solution should be wrapped in special HTML comments (see below) 
  to indicate removal in the sanitized version.

To delimit a markup solution to a manual question, wrap the solution in the HTML comments 
``<!-- BEGIN SOLUTION -->`` and ``<!-- END SOLUTION -->`` on their own lines to indicate that the 
content in between should be removed.

.. code-block:: markdown

    <!-- BEGIN SOLUTION -->
    solution goes here
    <!-- END SOLUTION -->

To use a custom Markdown prompt, include a ``<!-- BEGIN/END PROMPT -->`` block with a solution 
block, but add ``NO PROMPT`` inside the ``BEGIN SOLUTION`` comment:

.. code-block:: markdown

    <!-- BEGIN PROMPT -->
    prompt goes here
    <!-- END PROMPT -->

    <!-- BEGIN SOLUTION NO PROMPT -->
    solution goes here
    <!-- END SOLUTION -->

If ``NO PROMPT`` is not indicate, Otter Assign automatically replaces the solution with a line 
containing ``_Type your answer here, replacing this text._``.

An example of a manually-graded code question:

.. code-block:: markdown

    **Question 7:** Plot $f(x) = \cos e^x$ on $[0,10]$.

    ```
    BEGIN QUESTION
    name: q7
    manual: true
    ```

    ```{r}
    # BEGIN SOLUTION
    x = seq(0, 10, 0.01)
    y = cos(exp(x))
    ggplot(data.frame(x, y), aes(x=x, y=y)) +
        geom_line()
    # END SOLUTION
    ```

An example of a manually-graded written question (with no prompt):

.. code-block:: markdown

    **Question 5:** Simplify $\sum_{i=1}^n n$.

    ```
    BEGIN QUESTION
    name: q5
    manual: true
    ```

    <!-- BEGIN SOLUTION -->
    $\frac{n(n+1)}{2}$
    <!-- END SOLUTION -->

An example of a manuall-graded written question with a custom prompt:

.. code-block:: markdown

    **Question 6:** Fill in the blank.

    ```
    BEGIN QUESTION
    name: q6
    manual: true
    ```

    <!-- BEGIN PROMPT -->
    The mitochonrida is the ___________ of the cell.
    <!-- END PROMPT -->

    <!-- BEGIN SOLUTION NO PROMPT -->
    powerhouse
    <!-- END SOLUTION -->
