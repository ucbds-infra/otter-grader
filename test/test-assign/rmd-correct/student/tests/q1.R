test = list(
  name = "q1",
  cases = list(
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = 1,
      code = {
        test_that("q1a", {
            expect_true(is.numeric(x))
        })
      }
    ),
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = 1,
      code = {
        test_that("q1b", {
            expect_true(0 < x)
            expect_true(x < 100)
        })
      }
    )


  )
)