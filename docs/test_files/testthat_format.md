# R: `testthat` Format

Ottr tests rely on the testthat library to run tests on students' submissions. Because of this, ottr's tests look like unit tests with a couple of important caveats. The main different is that a global `test_metadata` variable is required, which is a multiline YAML-formatted string that contains configurations for each test case (e.g. point values, whether the test case is hidden). Each call to `testthat::test_that` in the test file must have a corresponding entry in the test metadata and these are linked together by the description of the test. An example test file would be:

```r
library(testthat)

test_metadata = "
name: q1
cases:
  - name: q1a
    points: 1
    hidden: false
  - name: q1b
    hidden: true
  - name: q1c
"

test_that("q1a", {
    expect_equal(a, 102.34)
})

test_that("q1a", {
    expected = c(1, 2, 3, 4)
    expect_equal(some_vec, expected)
})

test_that("q1a", {
    coeffs = model$coefficeints
    expected = c("(Intercept)" = 1.25, "Sepal.Length" = -3.40)
    expect_equal(coeffs, expected)
})
```

Each call to `testthat::test_that` has a description that matches the `name` of an element in the `cases` list in the  test metadata. If a student passes that test case, they are awarded the points in `case[points]` (defaults to 1). The `hidden` key of each case is used on Gradescope and determines whether a test case result is visible to students; this key defaults to `false`. The example above is worth 3 points in total, 1 for each test case, and the only visible test case is `q1a`.
