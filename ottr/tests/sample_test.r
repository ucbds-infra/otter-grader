library(testthat)

test_metadata = "
name: q1
cases:
  - name: q1a
    hidden: false
    points: 1
  - name: q1b
    hidden: true
    points: 1
"

test_that("q1a", {
  expect_equal(df$a, c(1:5))
  b = rep(2, 5)
  expect_equal(df$a + b, c(3:7))
})

test_that("q1b", {
  expect_equal(df$a2, c(1:5)^2)
})

