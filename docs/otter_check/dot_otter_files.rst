.. _otter_check_dot_otter_files:

Otter Configuration Files
=========================

In many use cases, the use of the ``otter.Notebook`` class by students requires some configurations 
to be set. These configurations are stored in a simple JSON-formatted file ending in the ``.otter`` 
extension. When ``otter.Notebook`` is instantiated, it globs all ``.otter`` files in the working 
directory and, if any are present, asserts that there is only 1 and loads this as the configuration. 
If no ``.otter`` config is found, it is assumed that there is no configuration file and, therefore, 
only features that don't require a config file are available.

The available keys in a ``.otter`` file are listed below, along with their default values. The only 
required key is ``notebook`` (i.e. if you use ``.otter`` file it must specify a value for 
``notebook``).

.. code-block:: python

    {
        "notebook": "",            # the notebook filename
        "save_environment": false, # whether to serialize the environment in the log during checks
        "ignore_modules": [],      # a list of modules whose functions to ignore during serialization
        "variables": {}            # a mapping of variable names -> types to resitrct during serialization
    }


Configuring the Serialization of Environments
---------------------------------------------

If you are using logs to grade assignemtns from serialized environments, the ``save_environment`` 
key must be set to ``true``. Any module names in the ``ignore_modules`` list will have their 
functions ignored during serialization. If ``variables`` is specified, it should be a dictionary 
mapping variables names to fully-qualified types; variables will only be serialized if they are 
present as keys in this dictionary and their type matches the specified type. An example of this use 
would be:

.. code-block:: json

    {
        "notebook": "hw00.ipynb",
        "save_environment": true,
        "variables": {
            "df": "pandas.core.frame.DataFrame",
            "fn": "builtins.function",
            "arr": "numpy.ndarray"
        }
    }

The function ``otter.utils.get_variable_type`` when called on an object will return this 
fully-qualified type string.

.. ipython:: python

    from otter.utils import get_variable_type
    import numpy as np
    import pandas as pd
    get_variable_type(np.array([]))
    get_variable_type(pd.DataFrame())
    fn = lambda x: x
    get_variable_type(fn)

More information about grading from serialized environments can be found in :ref:`logging`.
