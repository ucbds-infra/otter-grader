# Test Files

Otter requires OK-formatted tests to check student's work against. These have a very specific format, described in detail in the [OK documentation](https://okpy.github.io/documentation/client.html#ok-client-setup-ok-tests).

## OK Format Caveats

While otter uses OK format, there are a few caveats to the tests when using them with otter.

* Otter only allows a single suite in each test, although the suite can have any number of cases. This means that `test["suite"]` should be a list of length 1, whose only element is a `dict`.
* Otter has an additional key in the `test` dict, called `hidden`. `test["hidden"]` should evaluate to a boolean. This is used to indicate whether or not the test should be shown on Gradescope when students submit their work. If `test["hidden"]` is `True`, then all cases will be shown to students on Gradescope. **This is not to be confused with the `hidden` key of each case, which are ignored by otter.**

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
                    "hidden": False,    # ignored by otter
                    "locked": False,    # ignored by otter
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
            "scored": False,            # ignored by otter
            "setup": "",                # ignored by otter
            "teardown": "",             # ignored by otter
            "type": "doctest"           # the type of test; only "doctest" allowed
        },
    ]
}
```

## Writing OK Tests

You can find an online [OK test generator](https://oktests.herokuapp.com) that will assist you in generating these test files.
