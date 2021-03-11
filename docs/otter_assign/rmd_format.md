# RMarkdown Format

Otter Assign is compatible with Otter's R autograding system and currently supports Jupyter notebook and RMarkdown master documents. The format for using Otter Assign with R is very similar to the Python format with a few important differences.

## Assignment Metadata

As with Python, Otter Assign for R also allows you to specify various assignment generation arguments in an assignment metadata code block.

````
```
BEGIN ASSIGNMENT
init_cell: false
export_cell: true
...
```
````

This block is removed from both output files. Any unspecified keys will keep their default values. For more information about many of these arguments, see [Usage and Output](usage.md). The YAML block below lists all configurations **supported with Rmd files** and their defaults. Any keys that appear in the Python or R Juptyer notebook sections but not below will be ignored when using Otter Assign with Rmd files.

```yaml
requirements: requirements.txt # path to a requirements file for Gradescope; appended by default
overwrite_requirements: false  # whether to overwrite Otter's default requirements rather than appending
environment: environment.yml   # path to custom conda environment file
generate:                      # configurations for running Otter Generate; defaults to false
  points: null                 # number of points to scale assignment to on Gradescope
  threshold: null              # a pass/fail threshold for the assignment on Gradescope
  show_stdout: false           # whether to show grading stdout to students once grades are published
  show_hidden: false           # whether to show hidden test results to students once grades are published
files: []                      # a list of file paths to include in the distribution directories
```

## Autograded Questions

Here is an example question in an Otter Assign-formatted Rmd file:

````
**Question 1:** Find the radius of a circle that has a 90 deg. arc of length 2. Assign this value to `ans.1`

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
test_that("q1a", {
  expect_true(ans.1 > 1)
  expect_true(ans.1 < 2)
})
```

```{r}
## Hidden Test ##
test_that("q1b", {
  tol = 1e-5
  actual_answer = 1.27324
  expect_true(ans.1 > actual_answer - tol)
  expect_true(ans.1 < actual_answer + tol)
})
```
````

For code questions, a question is a some description markup, followed by a solution code blocks and zero or more test code blocks. The description must contain a code block (enclosed in triple backticks <code>\`\`\`</code>) that begins with `BEGIN QUESTION` on its own line, followed by YAML that defines metadata associated with the question.

The rest of the code block within the description cell must be YAML-formatted with the following fields (in any order):

* `name` (required) - a string identifier that is a legal file name (without an extension)
* `manual` (optional) - a boolean (default `false`); whether to include the response cell in a PDF for manual grading
* `points` (optional) - a number or list of numbers for the point values of each question. If a list of values, each case gets its corresponding value. If a single value, the number is divided by the number of cases so that a question with \\(n\\) cases has test cases worth \\(\frac{\text{points}}{n}\\) points.

As an example, the question metadata below indicates an autograded question `q1` with 3 subparts worth 1, 2, and 1 points, resp.

````
```
BEGIN QUESTION
name: q1
points: 
  - 1
  - 2
  - 1
```
````

### Solution Removal

Solution cells contain code formatted in such a way that the assign parser replaces lines or portions of lines with prespecified prompts. The format for solution cells in Rmd files is the same as in Python and R Jupyter notebooks, described [here](python_notebook_format.html#solution-removal). Otter Assign's solution removal for prompts is compatible with normal strings in R, including assigning these to a dummy variable so that there is no undesired output below the cell:

```r
# this is OK:
. = " # BEGIN PROMPT
some.var <- ...
" # END PROMPT
```

### Test Cells

The test cells are any code cells following the solution cell that begin with the comment `## Test ##` or `## Hidden Test ##` (case insensitive). A `Test` is distributed to students so that they can validate their work. A `Hidden Test` is not distributed to students, but is used for scoring their work. When writing tests, each test cell should be a single call to `testthat::test_that` and there should be **no code outside of the `test_that` call**. For example, instead of

```r
## Test ##
data = data.frame()
test_that("q1a", {
    # some test
})
```

do the following:

```r
## Test ##
test_that("q1a", {
    data = data.frame()
    # some test
})
```

## Manually Graded Questions

Otter Assign also supports manually-graded questions using a similar specification to the one described above. To indicate a manually-graded question, set `manual: true` in the question metadata. A manually-graded question is defined by three parts:

* A question metadata
* (Optionally) a prompt
* A solution

Manually-graded solution cells have two formats:

* If the response is code (e.g. making a plot), they can be delimited by solution removal syntax as above.
* If the response is markup, the the solution should be wrapped in special HTML comments (see below) to indicate removal in the sanitized version.

To delimit a markup solution to a manual question, wrap the solution in the HTML comments `<!-- BEGIN SOLUTION -->` and `<!-- END SOLUTION -->` on their own lines to indicate that the content in between should be removed.

```
<!-- BEGIN SOLUTION -->
solution goes here
<!-- END SOLUTION -->
```

To use a custom Markdown prompt, include a `<!-- BEGIN/END PROMPT -->` block with a solution block, but add `NO PROMPT` inside the `BEGIN SOLUTION` comment:

```
<!-- BEGIN PROMPT -->
prompt goes here
<!-- END PROMPT -->

<!-- BEGIN SOLUTION NO PROMPT -->
solution goes here
<!-- END SOLUTION -->
```

If `NO PROMPT` is not indicate, Otter Assign automatically replaces the solution with a line containing `_Type your answer here, replacing this text._`.

An example of a manually-graded code question:

````
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
````

An example of a manually-graded written question (with no prompt):

````
**Question 5:** Simplify $\sum_{i=1}^n n$.

```
BEGIN QUESTION
name: q5
manual: true
```

<!-- BEGIN SOLUTION -->
$\frac{n(n+1)}{2}$
<!-- END SOLUTION -->
````

An example of a manuall-graded written question with a custom prompt:

````
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
````
