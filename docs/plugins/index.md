# Plugins

```eval_rst
.. toctree::
   :maxdepth: 1
   :hidden:

   creating_plugins
```

Otter-Grader supports grading plugins that allow users to override the default behavior of Otter by injecting an importable class that is able to alter the state of execution.

## Using Plugins

Plugins can be configured in your `otter_config.json` file by listing the plugins as their fully-qualified importable names in the `plugins` key:

```json
{
    "plugins": [
        "mypackage.MyOtterPlugin"
    ]
}
```

To supply configurations for the plugins, put them as a subkey inside the `plugin_config` key of `otter_config.json`, using `{plugin}.PLUGIN_CONFIG_KEY` as the key. For example, if `mypackage.MyOtterPlugin.PLUGIN_CONFIG_KEY` is `"my_otter_plugin"`, the configurations for this plugin would look like

```json
{
    "plugins": [
        "mypackage.MyOtterPlugin"
    ],
    "plugin_config": {
        "my_otter_plugin": {
            "key1": "value1",
            "key2": "value2"
        }
    }
}
```

## Building Plugins

Plugins can be created as importable classes in packages that inherit from the `otter.plugins.AbstractOtterPlugin` class. For more information about creating plugins, see [Creating Plugins](creating_plugins.md).
