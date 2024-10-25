Python Format
=============

Python test files can follow one of two formats: exception-based or the OK format.


.. _test_files_python_exception_based:

Exception-Based Format
----------------------

The exception-based test file format relies on an idea similar to unit tests in pytest: an
instructor writes a series of test case functions that raise errors if the test case fails; if no
errors are raised, the test case passes.

Test case functions should be decorated with the ``otter.test_files.test_case`` decorator, which
holds metadata about the test case. The ``test_case`` decorator takes (optional) the arguments:

* ``name``: the name of the test case
* ``points``: the point value of the test case (default ``None``)
* ``hidden``: whether the test case is hidden (default ``False``)
* ``success_message``: a message to display to the student if the test case passes
* ``failure_message``: a message to display to the student if the test case fails

The test file should also declare the global variable ``name``, which should be a string containing
the name of the test case, and (optionally) ``points``, which should be the total point value of the
question. If this is absent (or set to ``None``), it will be inferred from the point values of each
test case as described :ref:`below <test_files_python_resolve_point_values>`. You can also set an
``all_or_nothing`` global variable to a boolean value indicating whether points for the test file
should be assigned on an all-or-nothing basis; that is, full points are assigned if all test cases
pass, otherwise 0 points are assigned (default ``False``). Because Otter also supports
OK-formatted test files, the global variable ``OK_FORMAT`` must be set to ``False`` in exception-based
test files.

When a test case fails and an error is raised, the full stack trace and error message will be shown
to the student. This means that you can use the error message to provide the students with information
about why the test failed:

.. code-block:: python

    assert fib(1) == 0, "Your fib function didn't handle the base case correctly."


Calling Test Case Functions
+++++++++++++++++++++++++++

Because test files are evaluated before the student's global environment is provided, test files will
not have access to the global environment during execution. However, Otter uses the test case function
arguments to pass elements from the global environment, or the global environment itself.

If the test case function has an argument name ``env``, the student's global environment will be 
passed in as the value for that argument. For any other argument name, the value of that variable in
the student's global environment will be passed in; if that variable is not present, it will default
to ``None``.

For example, the test function with the signature

.. code-block:: python

    test_square(square, env)

would be called like

.. code-block:: python

    test_square(square=globals().get("square"), env=globals())

in the student's environment.


Sample Test
+++++++++++

Here is a sample exception-based test file. The example below tests a student's ``sieve`` function,
which uses the Sieve of Eratosthenes to return a set of the ``n`` first prime numbers.

.. code-block:: python

    from otter.test_files import test_case

    OK_FORMAT = False

    name = "q1"
    points = 2

    @test_case()
    def test_low_primes(sieve):
        assert sieve(1) == set()
        assert sieve(2) == {2}
        assert sieve(3) == {3}

    @test_case(points=2, hidden=True)
    def test_higher_primes(env):
        assert env["sieve"](20) == {2, 3, 5, 7, 11, 13, 17, 19}
        assert sieve(100) == {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 
            61, 67, 71, 73, 79, 83, 89, 97}


.. _test_files_python_resolve_point_values:

Resolving Point Values
++++++++++++++++++++++

Point values for each test case and the question defined by the test file will be resolved as follows:

* If one or more test cases specify a point value and no point value is specified for the question, 
  each test case with unspecified point values is assumed to be worth 0 points unless all test cases 
  with specified points are worth 0 points; in this case, the question is assumed to be worth 1 point 
  and the test cases with unspecified points are equally weighted.
* If one or more test cases specify a point value and a point value *is* specified for the test file, 
  each test case with unspecified point values is assumed to be equally weighted and together are 
  worth the test file point value less the sum of specified point values. For example, in a 6-point 
  test file with 4 test cases where two test cases are each specified to be worth 2 points, each of 
  the other test cases is worth :math:`\frac{6-(2 + 2)}{2} = 1` point.)
* If no test cases specify a point value and a point value *is* specified for the test file, each 
  test case is assumed to be equally weighted and is assigned a point value of :math:`\frac{p}{n}` 
  where :math:`p` is the number of points for the test file and :math:`n` is the number of test 
  cases.
* If no test cases specify a point value and no point value is specified for the test file, the 
  test file is assumed to be worth 1 point and each test case is equally weighted.


OK Format
---------

You can also write OK-formatted tests to check students' work against. These have a very specific 
format, described in detail in the `OkPy documentation 
<https://okpy.github.io/documentation/client.html#ok-client-setup-ok-tests>`_. There is also a 
resource we developed on writing autograder tests that can be found `here 
<https://autograder-tests.rtfd.io>`_; this guide details things like the doctest format, the 
pitfalls of string comparison, and seeding tests.


.. _test_files_ok_format_caveats:

Caveats
+++++++

While Otter uses OK format, there are a few caveats to the tests when using them with Otter.

* Otter only allows a single suite in each test, although the suite can have any number of cases. 
  This means that ``test["suites"]`` should be a ``list`` of length 1, whose only element is a 
  ``dict``.
* Otter uses the ``"hidden"`` key of each test case only on Gradescope. When displaying results on 
  Gradescope, the ``test["suites"][0]["cases"][<int>]["hidden"]`` should evaluate to a boolean that 
  indicates whether or not the test is hidden. The behavior of showing and hiding tests is described 
  in :ref:`workflow_executing_submissions_gradescope`.


Writing OK Tests
++++++++++++++++

We recommend that you develop assignments using :ref:`Otter Assign <otter_assign>`, a tool 
which will generate these test files for you. If you already have assignments or would prefer to 
write them yourself, you can find an online `OK test generator <https://oktests.chrispyles.io>`_ 
that will assist you in generating these test files without using Otter Assign.

Because Otter also supports exception-based test files, the global variable ``OK_FORMAT`` must be 
set to ``True`` in OK-formatted test files.


Sample Test
+++++++++++

Here is an annotated sample OK test:

.. code-block:: python

    OK_FORMAT = True

    test = {
        "name": "q1",             # name of the test
        "points": 1,              # number of points for the entire suite
        "all_or_nothing": False,  # whether points for this test file are all-or-nothing
        "suites": [               # list of suites, only 1 suite allowed!
            {
                "cases": [                  # list of test cases
                    {                       # each case is a dict
                        "code": r"""        # test, formatted for Python interpreter
                        >>> 1 == 1          # note that in any subsequence line of a multiline
                        True                # statement, the prompt becomes ... (see below)
                        """,
                        "hidden": False,    # used to determine case visibility on Gradescope
                        "locked": False,    # ignored by Otter
                    }, 
                    {
                        "code": r"""
                        >>> for i in range(4):
                        ...     print(i == 1)
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
