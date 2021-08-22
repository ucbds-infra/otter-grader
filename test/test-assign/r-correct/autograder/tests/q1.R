test = list(
  name = "q1",
  cases = list(
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = 1,
      code = {
        
      }
    ),
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = 1,
      code = {
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
      name = NA,
      points = 2,
      code = {
        testthat::expect_equal(as.character(x), "2")
      }
    )
  )
)