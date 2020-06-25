library(testthat)

test_metadata = "
name: q1
cases:
  - name: q1a
    hidden: true
    points: 1
  - name: q1b
    hidden: false
    points: 1
  - name: q1c
    hidden: false
    points: 1
"

test_that("q1a", {
  expect_equal(a, 1)
  b = 2
  expect_equal(a + b, 3)
})

test_that("q1b", {
  expect_equal(b, 2)
  hidden = TRUE
  expect_false(hidden)
})

test_that("q1c", {
  expect_equal(b, 2)
  hidden = TRUE
  expect_false(hidden)
})
