test = list(
  name = "q3",
  cases = list(
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = ,
      code = {
        test_that("q3a", {
            expect_equal(nine, 9)
        })
      }
    ),
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = ,
      code = {
        test_that("q3b", {
            expect_equal(square(16), 256)
        })
      }
    ),
    ottr::TestCase$new(
      hidden = TRUE,
      name = NA,
      points = ,
      code = {
        test_that("q3c", {
            expect_equal(square(1), 1)
        })
      }
    )
  )
)