Intercell Seeding
=================

The Otter suite of tools supports intercell seeding, a process by which notebooks and scripts can be 
seeded for the generation of pseudorandom numbers, which is very advantageous for writing 
deterministic hidden tests. Otter implements this through the use of a ``--seed`` flag, which can be 
set to any integer. We discuss the inner mechanics of intercell seeding in this section, while the 
flags and other UI aspects are discussed in the sections corresponding to the Otter tool you're 
using.


Seeding Mechanics
-----------------

This section describes at a high-level how seeding is implemented in the autograder at the layer of 
code execution.


Notebooks
+++++++++

When seeding in notebooks, both NumPy and ``random`` are seeded using an integer provided by the 
instructor. The seeding code is added to each cell's source before running it through the executor,
meaning that the results of *every* cell are seeded with the same seed. For example, let's say we 
have the two cells below:

.. code-block:: python

    x = 2 ** np.arange(5)

and

.. code-block:: python

    y = np.random.normal(100)

they would be sent to the autograder as:

.. code-block:: python

    np.random.seed(SEED)
    random.seed(SEED)
    x = 2 ** np.arange(5)

and

.. code-block:: python

    np.random.seed(SEED)
    random.seed(SEED)
    y = np.random.normal(100)

where ``SEED`` is the seed you passed to Otter. This has two important consequences:

#. When writing assignments or using assignment generation tools like Otter Assign, the instructor 
must **seed the solutions themselves** before writing hidden tests in order to ensure they are 
grading the correct values.
#. Students will not have access to the random seed, so any values they compute in the notebook may 
be different from the results of their submission when it is run through the autograder.

With respect to (1), Otter Assign implements this behavior through the use of `seeding cells 
<otter_assign.html#intercell-seeding>`_ that are discarded in the output. This has a natural 
consequence of (2), which highlights the important of writing public tests that **do not** rely on 
the use of seeds unless they are provided in the distribution notebooks themselves (but I guess that 
renders the use of behind-the-scenes seeding useless, doesn't it?).


Python Scripts
++++++++++++++

Seeding Python files is relatively more simple. The implementation is similar to that of notebooks, 
but the script is only seeded once, at the beginning. Thus, the Python file below:

.. code-block:: python

    import numpy as np

    def sigmoid(t):
        return 1 / (1 + np.exp(-1 * t))

would be sent to the autograder as

.. code-block:: python

    np.random.seed(SEED)
    random.seed(SEED)
    import numpy as np

    def sigmoid(t):
        return 1 / (1 + np.exp(-1 * t))

You don't need to worry about importing NumPy and ``random`` before seeding as these modules are loaded by the autograder and provided in the global env that the script is executed against.


Cautions
--------

In this section, we highlight a few important things that bear repeating.


* **Make sure to use the same seed when creating assignments.** Also make sure that you pass this 
  seed to the ``--seed`` flag of any Otter tool you use.
* **Write public tests agnostic to the seed.** Students won't have access to it, remember!
