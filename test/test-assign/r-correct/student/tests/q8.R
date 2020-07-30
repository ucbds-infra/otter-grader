library(testthat)

test_metadata = "
cases:
- hidden: false
  name: q8a
  points: 1
name: q8

"

test_that("q8a", {
    expect_equal(length(z), 10)
})
