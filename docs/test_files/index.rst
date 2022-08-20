.. _test_files:

Test Files
==========

.. toctree::
    :maxdepth: 1
    :hidden:

    python_format
    r_format

Otter has different test file formats depending on which language you are grading. Python test files
can follow an exception-based unit-test-esque format like pytest, or can
follow the OK format, a legacy of the OkPy autograder that Otter inherits from. R test files are 
like unit tests and rely on ``TestCase`` classes exported by the ``ottr`` package.
