test = list(
  name = "q3",
  cases = list(
    ottr::TestCase$new(
      hidden = FALSE,
      name = "q3a",
      points = ,
      code = {
        test_that("q3a", {
            expect_equal(nine, 9)
        })
      }
    ),
    ottr::TestCase$new(
      hidden = FALSE,
      name = "q3b",
      points = ,
      code = {
        test_that("q3b", {
            expect_equal(square(16), 256)
        })
      }
    )

  )
)