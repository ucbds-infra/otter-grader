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
    ),
    ottr::TestCase$new(
      hidden = TRUE,
      name = NA,
      points = 1,
      code = {
        testthat::expect_equal(x, 2)
      }
    ),
    ottr::TestCase$new(
      hidden = TRUE,
      name = "q1d",
      points = 2,
      success_message = "congrats",
      code = {
        testthat::expect_equal(as.character(x), "2")
      }
    )
  )
)