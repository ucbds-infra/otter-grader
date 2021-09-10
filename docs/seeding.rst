.. _seeding:

Intercell Seeding
=================

The Otter suite of tools supports intercell seeding, a process by which notebooks and scripts can be 
seeded for the generation of pseudorandom numbers, which is very advantageous for writing 
deterministic hidden tests. This section discusses the inner mechanics of intercell seeding, while the 
flags and other UI aspects are discussed in the sections corresponding to the Otter tool you're 
using.


Seeding Mechanics
-----------------

This section describes at a high-level how seeding is implemented in the autograder at the layer of 
code execution. There are two methods of seeding: the use of a seed variable, and seeding the 
libraries themselves.

The examples in this section are all in Python, but they also work the same in R.


Seed Variables
++++++++++++++

The use of seed variables is configured by setting both the ``seed`` and ``seed_variable`` configurations
in your ``otter_config.json``:

.. code-block:: json

    {
        "seed": 42,
        "seed_variable": "rng_seed"
    }


Notebooks
?????????

When seeding in notebooks, an assignment of the variable name indicated by ``seed_variable`` is
added at the top of every cell. In this way, cells that use the seed variable to create an RNG or
seed libraries can have their seed changed from the default at runtime.

For example, let's say we have the configuration above and the two cells below:

.. code-block:: python

    x = 2 ** np.arange(5)

and

.. code-block:: python

    rng = np.random.default_rng(rng_seed)
    y = rng.normal(100)

They would be sent to the autograder as:

.. code-block:: python

    rng_seed = 42
    x = 2 ** np.arange(5)

and

.. code-block:: python

    rng_seed = 42
    rng = np.random.default_rng(rng_seed)
    y = rng.normal(100)

Note that the initial value of the seed variable must be set in a separate cell from any of its uses,
or the original value will override autograder value.


Python Scripts
??????????????

Seed variables currently do not support Python scripts.


Seeding Libraries
+++++++++++++++++

Seeding libraries is configured by setting the ``seed`` configuration in your ``otter_config.json``:

.. code-block:: json

    {
        "seed": 42
    }


Notebooks
?????????

When seeding in notebooks, both NumPy and ``random`` are seeded using an integer provided by the 
instructor. The seeding code is added to each cell's source before running it through the executor,
meaning that the results of *every* cell are seeded with the same seed. For example, let's say we 
have the configuration above and the two cells below:

.. code-block:: python

    x = 2 ** np.arange(5)

and

.. code-block:: python

    y = np.random.normal(100)

They would be sent to the autograder as:

.. code-block:: python

    np.random.seed(42)
    random.seed(42)
    x = 2 ** np.arange(5)

and

.. code-block:: python

    np.random.seed(42)
    random.seed(42)
    y = np.random.normal(100)


Python Scripts
??????????????

Seeding Python files is relatively more simple. The implementation is similar to that of notebooks, 
but the script is only seeded once, at the beginning. Thus, the Python file below:

.. code-block:: python

    import numpy as np

    def sigmoid(t):
        return 1 / (1 + np.exp(-1 * t))

would be sent to the autograder as

.. code-block:: python

    np.random.seed(42)
    random.seed(42)
    import numpy as np

    def sigmoid(t):
        return 1 / (1 + np.exp(-1 * t))

You don't need to worry about importing NumPy and ``random`` before seeding as these modules are 
loaded by the autograder and provided in the global environment that the script is executed against.


Caveats
--------

Remekber, when writing assignments or using assignment generation tools like Otter Assign, the instructor 
must **seed the solutions themselves** before writing hidden tests in order to ensure they are 
grading the correct values. Also, students will not have access to the random seed, so any values 
they compute in the notebook may be different from the results of their submission when it is run 
through the autograder.
