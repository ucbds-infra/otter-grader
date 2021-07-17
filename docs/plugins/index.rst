.. _plugins:

Plugins
=======

.. toctree::
    :maxdepth: 1
    :hidden:

    builtin/index
    creating_plugins

Otter-Grader supports grading plugins that allow users to override the default behavior of Otter by 
injecting an importable class that is able to alter the state of execution.


Using Plugins
-------------

Plugins can be configured in your ``otter_config.json`` file by listing the plugins as their 
fully-qualified importable names in the ``plugins`` key:

.. code-block:: json

    {
        "plugins": [
            "mypackage.MyOtterPlugin"
        ]
    }

To supply configurations for the plugins, add the plugin to ``plugins`` as a dictionary mapping a 
single key, the plugin importable name, to a dictionary of configurations. For example, if we needed 
``mypackage.MyOtterPlugin`` with  configurations but ``mypackage.MyOtherOtterPlugin`` required none, 
the configurations for these plugins would look like

.. code-block:: json

    {
        "plugins": [
            {
                "mypackage.MyOtterPlugin": {
                    "key1": "value1",
                    "key2": "value2"
                }
            },
            "mypackage.MyOtherOtterPlugin"
        ]
    }


Building Plugins
----------------

Plugins can be created as importable classes in packages that inherit from the 
``otter.plugins.AbstractOtterPlugin`` class. For more information about creating plugins, see 
:ref:`plugins_creating_plugins`.
