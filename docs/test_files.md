# Test Files

Otter requires OK-formatted tests to check students' work against. These have a very specific format, described in detail in the [OK documentation](https://okpy.github.io/documentation/client.html#ok-client-setup-ok-tests).

## OK Format Caveats

While Otter uses OK format, there are a few caveats to the tests when using them with Otter.

* Otter only allows a single suite in each test, although the suite can have any number of cases. This means that `test["suite"]` should be a list of length 1, whose only element is a `dict`.
* Otter has an additional key in the `test` dict, called `hidden`. `test["hidden"]` should evaluate to a boolean. This is used to indicate whether or not the test should be shown on Gradescope when students submit their work. If `test["hidden"]` is `True`, then all cases will be shown to students on Gradescope. **This is not to be confused with the `hidden` key of each case, which are ignored by Otter.**

## Writing OK Tests

We recommend that you develop assignments using [Otter Assign](otter_assign.md), a tool which will generate these test files for you. If you already have assignments or would prefer to write them yourself, you can find an online [OK test generator](https://oktests.chrispyles.io) that will assist you in generating these test files without using Otter Assign.

## Sample Test

Here is an annotated sample OK test:

```python
test = {
    "name": "q1",       # name of the test
    "points": 1,        # number of points for the entire suite
    "hidden": False,    # whether the test is hidden on Gradescope
    "suites": [         # list of suites, only 1 suite allowed!
        {
            "cases": [                  # list of test cases
                {                       # each case is a dict
                    "code": r"""        # test, formatted for Python interpreter
                    >>> 1 == 1          # note that in any subsequence line of a multiline
                    True                # statement, the prompt becomes ... (see below)
                    """,
                    "hidden": False,    # ignored by Otter
                    "locked": False,    # ignored by Otter
                }, 
                {
                    "code": r"""
                    >>> for i in range(4):
                    ... 	print(i == 1)
                    False
                    True
                    False
                    False
                    """,
                    "hidden": False,
                    "locked": False,
                }, 
            ],
            "scored": False,            # ignored by Otter
            "setup": "",                # ignored by Otter
            "teardown": "",             # ignored by Otter
            "type": "doctest"           # the type of test; only "doctest" allowed
        },
    ]
}
```
