R Format
========

Ottr tests are constructed by creating a JSON-like object (a ``list``) that has a list of instances
of the R6 class ``ottr::TestCase``. The body of each test case is a block of code that should raise
an error if the test fails, and no error if it passes. The list of test cases should be declared in
a global ``test`` variable. The structure of the test file looks something like:

.. code-block:: r

    test = list(
        name = "q1",
        cases = list(
            ottr::TestCase$new(
                name = "q1a",
                code = {
                    testthat::expect_true(ans.1 > 1)
                    testthat::expect_true(ans.1 < 2)
                }
            ),
            ottr::TestCase$new(
                name = "q1b",
                hidden = TRUE,
                code = {
                    tol = 1e-5
                    actual_answer = 1.27324
                    testthat::expect_true(ans.1 > actual_answer - tol)
                    testthat::expect_true(ans.1 < actual_answer + tol)
                }
            )
        )
    )

Note that the example above uses the ``expect_*`` functions exported by ``testthat`` to assert
conditions that raise errors. The constructor for ``ottr::TestCase`` accepts the following 
arguments:

- ``name``: the name of the test case
- ``points``: the point value of the test case
- ``hidden``: whether this is a hidden test
- ``code``: the body of the test
