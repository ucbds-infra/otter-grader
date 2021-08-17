test = list(
  name = "q3",
  cases = list(
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = 0.6666666666666666,
      code = {
        test_that("q3a", {
            expect_equal(nine, 9)
        })
      }
    ),
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = 0.6666666666666666,
      code = {
        test_that("q3b", {
            expect_equal(square(16), 256)
        })
      }
    )

  )
)