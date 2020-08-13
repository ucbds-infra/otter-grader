library(testthat)

test_metadata = "
cases:
- hidden: false
  name: q3a
  points: 0.6666666666666666
- hidden: false
  name: q3b
  points: 0.6666666666666666
name: q3

"

test_that("q3a", {
    expect_equal(nine, 9)
})

test_that("q3b", {
    expect_equal(square(16), 256)
})
