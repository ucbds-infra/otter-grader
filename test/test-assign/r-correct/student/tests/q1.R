library(testthat)

test_metadata = "
cases:
- hidden: false
  name: q1a
  points: 1
- hidden: false
  name: q1b
  points: 1
name: q1

"

test_that("q1a", {
    expect_true(is.numeric(x))
})

test_that("q1b", {
    expect_true(0 < x)
    expect_true(x < 100)
})
