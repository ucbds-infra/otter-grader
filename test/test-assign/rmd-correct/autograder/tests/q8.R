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
    ),
    ottr::TestCase$new(
      hidden = TRUE,
      name = NA,
      points = 0.5,
      code = {
        test_that("q8b", {
            actual = c(
                6.74191689429334,
                2.87060365720782,
                4.72625682267468,
                5.26572520992208, 
                4.808536646282, 
                3.78775096781703, 
                7.02304399487788, 
                3.8106819231738, 
                8.03684742775408, 
                3.87457180189516
            )
            expect_equal(actual, z)
        })
      }
    )
  )
)