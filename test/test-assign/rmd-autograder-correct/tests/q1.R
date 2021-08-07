test = list(
  name = "q1",
  cases = list(
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = ,
      code = {
        test_that("q1a", {
            expect_true(is.numeric(x))
        })
      }
    ),
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = ,
      code = {
        test_that("q1b", {
            expect_true(0 < x)
            expect_true(x < 100)
        })
      }
    ),
    ottr::TestCase$new(
      hidden = TRUE,
      name = NA,
      points = ,
      code = {
        test_that("q1c", {
            expect_equal(x, 2)
        })
      }
    ),
    ottr::TestCase$new(
      hidden = TRUE,
      name = NA,
      points = ,
      code = {
        test_that("q1d", {
            expect_equal(as.character(x), "2")
        })
      }
    )
  )
)