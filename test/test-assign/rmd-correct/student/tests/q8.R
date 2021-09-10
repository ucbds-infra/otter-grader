test = list(
  name = "q8",
  cases = list(
    ottr::TestCase$new(
      hidden = FALSE,
      name = NA,
      points = 0.5,
      code = {
        test_that("q8a", {
            expect_equal(length(z), 10)
        })
      }
    )

  )
)