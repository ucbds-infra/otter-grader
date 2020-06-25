library(testthat)

test_metadata = "
name: q2
points: 2
cases:
  - name: q2a
    hidden: true
    points: 2
  - name: q2b
    hidden: false
    points: 2
"

test_that("q2a", {
  expect_equal(a, 1)
})

test_that("q2b", {
  expect_equal(b, 2)
})
