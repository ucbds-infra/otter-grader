Notebook Format
===============

Otter's notebook format groups prompts, solutions, and tests together into questions. Autograder tests 
are specified as cells in the notebook and their output is used as the expected output of the 
autograder when generating tests. Each question has metadata, expressed in raw YAML config cell
when the question is declared.

Note that the major difference between v0 format and v1 format is the use of raw notebook cells as
delimiters. Each boundary cell denotes the start or end of a block and contains *valid YAML syntax*.
First-line comments are used in these YAML raw cells to denote what type of block is being entered
or ended.

**In the v1 format, Python and R notebooks follow the same structure.** There are some features
available in Python that are not available in R, and these are noted below, but otherwise the formats
are the same.


.. _otter_assign_v1_assignment_metadata:

Assignment Config
-----------------

In addition to various command line arguments discussed below, Otter Assign also allows you to 
specify various assignment generation arguments in an assignment config cell. These are very 
similar to the question config cells described in the next section. Assignment config, included 
by convention as the first cell of the notebook, places YAML-formatted configurations in a raw cell
that begins with the comment ``# ASSIGNMENT CONFIG``.

.. code-block:: yaml

    # ASSIGNMENT CONFIG
    init_cell: false
    export_cell: true
    generate: true
    # etc.

This cell is removed from both output notebooks. These configurations can be **overwritten** by 
their command line counterparts (if present). The options, their defaults, and descriptions are 
listed below. Any unspecified keys will keep their default values. For more information about many 
of these arguments, see :ref:`otter_assign_usage`. Any keys that map to 
sub-dictionaries (e.g. ``export_cell``, ``generate``) can have their behaviors turned off by 
changing their value to ``false``. The only one that defaults to true (with the specified sub-key 
defaults) is ``export_cell``.

.. fica:: otter.assign.assignment.Assignment

For assignments that share several common configurations, these can be specified in a separate YAML
file whose path is passed to the ``config_file`` key. When this key is encountered, Otter will read
the file and load the configurations defined therein into the assignment config for the notebook
it's running. Any keys specified in the notebook itself will override values in the file.

.. code-block:: yaml

    # ASSIGNMENT CONFIG
    config_file: ../assignment_config.yml
    files:
        - data.csv

All paths specified in the configuration should be **relative to the directory containing the master 
notebook**. If, for example, you were running Otter Assign on the ``lab00.ipynb`` notebook in the 
structure below:

.. code-block::

    dev
    ├── lab
    │   └── lab00
    │       ├── data
    │       │   └── data.csv
    │       ├── lab00.ipynb
    │       └── utils.py
    └── requirements.txt

and you wanted your requirements from ``dev/requirements.txt`` to be included, your configuration would 
look something like this:

.. code-block:: yaml

    requirements: ../../requirements.txt
    files:
        - data/data.csv
        - utils.py

The `requirements` key of the assignment config can also be formatted as a list of package names in
lieu of a path to a `requirements.txt` file; for exmaple:

.. code-block:: yaml

    requirements:
        - pandas
        - numpy
        - scipy

This structure is also compatible with the `overwrite_requirements` key.

A note about Otter Generate: the ``generate`` key of the assignment config has two forms. If you 
just want to generate and require no additional arguments, set ``generate: true`` in the YAML and 
Otter Assign will simply run ``otter generate`` from the autograder directory (this will also 
include any files passed to ``files``, whose paths should be **relative to the directory containing 
the notebook**, not to the directory of execution). If you require additional arguments, e.g. 
``points`` or ``show_stdout``, then set ``generate`` to a nested dictionary of these parameters and 
their values:

.. code-block:: yaml

    generate:
        seed: 42
        show_stdout: true
        show_hidden: true

You can also set the autograder up to automatically upload PDFs to student submissions to another 
Gradescope assignment by setting the necessary keys under ``generate``:

.. code-block:: yaml

    generate:
        token: YOUR_TOKEN      # optional
        course_id: 1234        # required
        assignment_id: 5678    # required
        filtering: true        # true is the default

You can run the following to retrieve your token:

.. code-block:: python

    from otter.generate.token import APIClient
    print(APIClient.get_token())

If you don't specify a token, you will be prompted for your username and password when you run Otter
Assign; optionally, you can specify these via the command line with the ``--username`` and
``--password`` flags.

Any configurations in your ``generate`` key will be put into an ``otter_config.json`` and used when
running Otter Generate.

If you are grading from the log or would like to store students' environments in the log, use the 
``save_environment`` key. If this key is set to ``true``, Otter will serialize the stuednt's 
environment whenever a check is run, as described in :ref:`logging`. To restrict the 
serialization of variables to specific names and types, use the ``variables`` key, which maps 
variable names to fully-qualified type strings. The ``ignore_modules`` key is used to ignore 
functions from specific modules. To turn on grading from the log on Gradescope, set 
``generate[grade_from_log]`` to ``true``. The configuration below turns on the serialization of 
environments, storing only variables of the name ``df`` that are pandas dataframes.

.. code-block:: yaml

    save_environment: true
    variables:
        df: pandas.core.frame.DataFrame

As an example, the following assignment config includes an export cell but no filtering, no init 
cell, and passes the configurations ``points`` and ``seed`` to Otter Generate via the 
``otter_config.json``.

.. code-block:: yaml

    # ASSIGNMENT CONFIG
    export_cell:
        filtering: false
    init_cell: false
    generate:
        points: 3
        seed: 0

You can also configure assignments created with Otter Assign to ensure that students submit to the
correct assignment by setting the ``name`` key in the assignment config. When this is set, Otter
Assign adds the provided name to the notebook metadata and the autograder configuration zip file;
this configures the autograder to fail if the student uploads a notebook with a different assignment
name in the metadata.

.. code-block:: yaml

    # ASSIGNMENT CONFIG
    name: hw01

You can find more information about how Otter performs assignment name verification
:ref:`here<workflow_execution_submissions_assignment_name_verification>`.

By default, Otter's grading images uses Python 3.7. If you need a different version, you can
specify one using the ``python_version`` config:

.. code-block:: yaml

    # ASSIGNMENT CONFIG
    python_version: 3.9


.. _otter_assign_v1_seed_variables:

Intercell Seeding
+++++++++++++++++

Python assignments support :ref:`intercell seeding <seeding>`, and there are two flavors of this. 
The first involves the use of a seed variable, and is configured in the assignment config; this 
allows you to use tools like ``np.random.default_rng`` instead of just ``np.random.seed``. The 
second flavor involves comments in code cells, and is described 
:ref:`below <otter_assign_v1_python_seeding>`.

To use a seed variable, specify the name of the variable, the autograder seed value, and the student
seed value in your assignment config.

.. code-block:: yaml

    # ASSIGNMENT CONFIG
    seed:
        variable: rng_seed
        autograder_value: 42
        student_value: 713

With this type of seeding, you do not need to specify the seed inside the ``generate`` key; this
automatically taken care of by Otter Assign.

Then, in a cell of your notebook, define the seed variable *with the autograder value*. This value
needs to be defined in a separate cell from any of its uses and the variable name cannot be used
for anything other than seeding RNGs. This is because it the variable will be redefined in the 
student's submission at the top of every cell. We recommend defining it in, for example, your 
imports cell.

.. code-block:: python

    import numpy as np
    rng_seed = 42

To use the seed, just use the variable as normal:

.. code-block:: python

    rng = np.random.default_rng(rng_seed)
    rvs = [rng.random() for _ in range(1000)] # SOLUTION

Or, in R:

.. code-block:: r

    set.seed(rng_seed)
    runif(1000)

If you use this method of intercell seeding, the solutions notebook will contain the original value
of the seed, but the student notebook will contain the student value:

.. code-block:: python

    # from the student notebook
    import numpy as np
    rng_seed = 713

When you do this, Otter Generate will be configured to overwrite the seed variable in each submission,
allowing intercell seeding to function as normal.

Remember that the student seed is different from the autograder seed, so any public tests cannot be
deterministic otherwise they will fail on the student's machine. Also note that only one seed is
available, so each RNG must use the same seed.

You can find more information about intercell seeding :ref:`here <seeding>`.


Autograded Questions
--------------------

Here is an example question in an Otter Assign-formatted question:

.. raw:: html

    <iframe src="../../_static/notebooks/html/assign-code-question-v1.html"></iframe>


Note the use of the delimiting raw cells and the placement of question config in the ``# BEGIN
QUESTION`` cell. The question config can contain the following fields (in any order):

.. fica:: otter.assign.question_config.QuestionConfig

As an example, the question config below indicates an autograded question ``q1`` that should be
included in the filtered PDF.

.. code-block:: yaml

    # BEGIN QUESTION
    name: q1
    export: true


.. _otter_assign_v1_python_solution_removal:

Solution Removal
++++++++++++++++

Solution cells contain code formatted in such a way that the assign parser replaces lines or portions 
of lines with prespecified prompts. Otter uses the same solution replacement rules as jAssign. From 
the `jAssign docs <https://github.com/okpy/jassign/blob/master/docs/notebook-format.md>`_:

* A line ending in ``# SOLUTION`` will be replaced by ``...`` (or ``NULL # YOUR CODE HERE`` in R), 
  properly indented. If that line is an assignment statement, then only the expression(s) after the
  ``=`` symbol (or the ``<-`` symbol in R) will be replaced.
* A line ending in ``# SOLUTION NO PROMPT`` or ``# SEED`` will be removed.
* A line ``# BEGIN SOLUTION`` or ``# BEGIN SOLUTION NO PROMPT`` must be paired with
  a later line ``# END SOLUTION``. All lines in between are replaced with ``...`` 
  (or ``# YOUR CODE HERE`` in R) or removed completely in the case of ``NO PROMPT``.
* A line ``""" # BEGIN PROMPT`` must be paired with a later line ``""" # END
  PROMPT``. The contents of this multiline string (excluding the ``# BEGIN
  PROMPT``) appears in the student cell. Single or double quotes are allowed.
  Optionally, a semicolon can be used to suppress output: ``"""; # END PROMPT``



.. code-block:: python

    def square(x):
        y = x * x # SOLUTION NO PROMPT
        return y # SOLUTION

    nine = square(3) # SOLUTION

would be presented to students as

.. code-block:: python

    def square(x):
        ...

    nine = ...

And

.. code-block:: python

    pi = 3.14
    if True:
        # BEGIN SOLUTION
        radius = 3
        area = radius * pi * pi
        # END SOLUTION
        print('A circle with radius', radius, 'has area', area)

    def circumference(r):
        # BEGIN SOLUTION NO PROMPT
        return 2 * pi * r
        # END SOLUTION
        """ # BEGIN PROMPT
        # Next, define a circumference function.
        pass
        """; # END PROMPT

would be presented to students as

.. code-block:: python

    pi = 3.14
    if True:
        ...
        print('A circle with radius', radius, 'has area', area)

    def circumference(r):
        # Next, define a circumference function.
        pass

For R,

.. code-block:: r

    # BEGIN SOLUTION
    square <- function(x) {
        return(x ^ 2)
    }
    # END SOLUTION
    x2 <- square(25)

would be presented to students  as

.. code-block:: r

    ...
    x2 <- square(25)


Test Cells
++++++++++

Any cells within the ``# BEGIN TESTS`` and ``# END TESTS`` boundary cells are considered test cells.
Each test cell corresponds to a single test case. There are two types of tests: public and hidden tests.
Tests are public by default but can be hidden by adding the ``# HIDDEN`` comment as the first line
of the cell. A hidden test is not distributed to students, but is used for scoring their work.

Test cells also support test case-level metadata. If your test requires metadata beyond whether the 
test is hidden or not, specify the test by including a mutliline string at the top of the cell that 
includes YAML-formatted test config. For example,

.. code-block:: python

    """ # BEGIN TEST CONFIG
    points: 1
    success_message: Good job!
    """ # END TEST CONFIG
    ...  # your test goes here

The test config supports the following keys with the defaults specified below:

.. code-block:: yaml

    hidden: false          # whether the test is hidden
    points: null           # the point value of the test
    success_message: null  # a messsge to show to the student when the test case passes
    failure_message: null  # a messsge to show to the student when the test case fails

Because points can be specified at the question level and at the test case level, Otter will resolve
the point value of each test case as described :ref:`here <test_files_python_resolve_point_values>`.

**If a question has no solution cell provided**, the question will either be removed from the output 
notebook entirely if it has only hidden tests or will be replaced with an unprompted 
``Notebook.check`` cell that runs those tests. In either case, the test files are written, but this 
provides a way of defining additional test cases that do not have public versions. Note, however, 
that the lack of a ``Notebook.check`` cell for questions with only hidden tests means that the tests 
are run *at the end of execution*, and therefore are not robust to variable name collisions.

Because Otter supports two different types of test files, test cells can be written in two different 
ways.


OK-Formatted Test Cells
???????????????????????

To use OK-formatted tests, which are the default for Otter Assign, you can write the test code in a test 
cell; Otter Assign will parse the output of the cell to write a doctest for the question, which will 
be used for the test case. **Make sure that only the last line of the cell produces any output, 
otherwise the test will fail.**


Exception-Based Test Cells
??????????????????????????

To use Otter's exception-based tests, you must set ``tests: ok_format: false`` in your assignment 
config. Your test cells should define
a test case function as described :ref:`here <test_files_python_exception_based>`. You can run the
test in the master notebook by calling the function, but you should make  sure that this call is 
"ignored" by Otter Assign so that it's not included in the test file by appending ``# IGNORE`` to the
end of line. You should *not* add the ``test_case`` decorator; Otter Assign will do this for you. 

For example,

.. code-block:: python

    """ # BEGIN TEST CONFIG
    points: 0.5
    """ # END TEST CONFIG
    def test_validity(arr):
        assert len(arr) == 10
        assert (0 <= arr <= 1).all()

    test_validity(arr)  # IGNORE

It is important to note that the exception-based test files are executed before the student's global
environment is provided, so no work should be performed outside the test case function that relies
on student code, and any libraries or other variables declared in the student's environment must be
passed in as arguments, otherwise the test will fail.

For example,

.. code-block:: python

    def test_values(arr):
        assert np.allclose(arr, [1.2, 3.4, 5.6])  # this will fail, because np is not in the test file

    def test_values(np, arr):
        assert np.allclose(arr, [1.2, 3.4, 5.6])  # this works

    def test_values(env):
        assert env["np"].allclose(env["arr"], [1.2, 3.4, 5.6])  # this also works


.. _otter_assign_v1_r_test_cells:

R Test Cells
????????????

Test cells in R notebooks are like a cross between exception-based test cells and OK-formatted test
cells: the checks in the cell do not need to be wrapped in a function, but the passing or failing of
the test is determined by whether it raises an error, not by checking the output. For example,

.. code-block:: r

    . = " # BEGIN TEST CONFIG
    hidden: true
    points: 1
    " # END TEST CONFIG
    testthat::expect_equal(sieve(3), c(2, 3))


.. _otter_assign_v1_python_seeding:

Intercell Seeding
+++++++++++++++++

The second flavor of intercell seeding involves writing a line that ends with ``# SEED``; when Otter 
Assign runs, this line will be removed from the student version of the notebook. This allows 
instructors to write code with deterministic output, with which hidden tests can be generated.

For example, the first line of the cell below would be removed in the student version of the notebook.

.. code-block:: python

    np.random.seed(42) # SEED
    rvs = [np.random.random() for _ in range(1000)] # SOLUTION

The same caveats apply for this type of seeding as :ref:`above <otter_assign_v1_seed_variables>`.


R Example
+++++++++

Here is an example autograded question for R:

.. raw:: html

    <iframe src="../../_static/notebooks/html/assign-r-code-question-v1.html"></iframe>


.. _otter_assign_v1_python_manual_questions:

Manually-Graded Questions
-------------------------

Otter Assign also supports manually-graded questions using a similar specification to the one 
described above. To indicate a manually-graded question, set ``manual: true`` in the question 
config. 

.. raw:: html

    <iframe src="../../_static/notebooks/html/assign-written-question-v1.html"></iframe>

A manually-graded question can have an optional prompt block and a required solution block. If the
solution has any code cells, they will have their syntax transformed by the solution removal rules
listed above.

If there is a prompt for manually-graded questions, then this prompt is included unchanged in the 
output. If none is present, Otter Assign automatically adds a Markdown cell with the contents 
``_Type your answer here, replacing this text._`` if the solution block has any Markdown cells in it.

Here is an example of a manually-graded code question:

.. raw:: html

    <iframe src="../../_static/notebooks/html/assign-manual-code-question-v1.html"></iframe>

Manually graded questions are automatically enclosed in ``<!-- BEGIN QUESTION -->`` and ``<!-- END 
QUESTION -->`` tags by Otter Assign so that only these questions are exported to the PDF when 
filtering is turned on (the default). In the autograder notebook, this includes the question cell, 
prompt cell, and solution cell. In the student notebook, this includes only the question and prompt 
cells. The ``<!-- END QUESTION -->`` tag is automatically inserted at the top of the next cell if it 
is a Markdown cell or in a new Markdown cell before the next cell if it is not.


Ignoring Cells
--------------

For any cells that you don't want to be included in *either* of the output notebooks that are 
present in the master notebook, include a line at the top of the cell with the ``## Ignore ##`` 
comment (case insensitive) just like with test cells. Note that this also works for Markdown cells 
with the same syntax.

.. code-block:: python

    ## Ignore ##
    print("This cell won't appear in the output.")


Student-Facing Plugins
----------------------

Otter supports student-facing plugin events via the ``otter.Notebook.run_plugin`` method. To include 
a student-facing plugin call in the resulting versions of your master notebook, add a multiline 
plugin config string to a code cell of your choosing. The plugin config should be YAML-formatted as 
a mutliline comment-delimited string, similar to the solution and prompt blocks above. The comments 
``# BEGIN PLUGIN`` and ``# END PLUGIN`` should be used on the lines with the triple-quotes to delimit 
the YAML's boundaries. There is one required configuration: the plugin name, which should be a 
fully-qualified importable string that evaluates to a plugin that inherits from 
``otter.plugins.AbstractOtterPlugin``. 

There are two optional configurations: ``args`` and ``kwargs``. ``args`` should be a list of 
additional arguments to pass to the plugin. These will be left unquoted as-is, so you can pass 
variables in the notebook to the plugin just by listing them. ``kwargs`` should be a dictionary that 
mappins keyword argument names to values; thse will also be added to the call in ``key=value`` 
format.

Here is an example of plugin replacement in Otter Assign:

.. raw:: html

    <iframe src="../../_static/notebooks/html/assign-plugin.html"></iframe>

*Note that student-facing plugins are not supported with R assignments.*


Running on Non-standard Python Environments
-------------------------------------------

For non-standard Python notebook environments (which use their own interpreters, such as Colab or
Jupyterlite), some Otter features are disabled and the the notebooks that are produced for running
on those environments are slightly different. To indicate that the notebook produce by Otter Assign
is going to be run in such an environment, use the ``runs_on`` assignment configuration. It
currently supports these values:

* ``default``, indicating a normal IPython environment (the default value)
* ``colab``, indicating that the notebook will be used on Google Colab
* ``jupyterlite``, indicating that the notebook will be used on Jupyterlite (or any environment
  using the Pyolite kernel)


Sample Notebook
---------------

You can find a sample Python notebook `here <https://github.com/ucbds-infra/otter-grader/blob/master/docs/_static/notebooks/assign-full-example-v1.ipynb>`_.
