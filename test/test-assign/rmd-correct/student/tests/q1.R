test = list(
  name = "q1",
  cases = list(
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = 1,
      code = {
        testthat::expect_true(is.numeric(x))
      }
    ),
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = 1,
      code = {
        testthat::expect_true(0 < x)
        testthat::expect_true(x < 100)
      }
    )
  )
)