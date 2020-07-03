# Otter Configuration Files

In many use cases, the use of the `otter.Notebook` class by students requires some configurations to be set. These configurations are stored in a simple JSON-formatted file ending in the `.otter` extension. When `otter.Notebook` is instantiated, it globs all `.otter` files in the working directory and, if any are present, asserts that there is only 1 and loads this as the configuration. If no `.otter` config is found, it is assumed that there is no configuration file and, therefore, only features that don't require a config file are available.

The available keys in a `.otter` file are listed below, along with their default values. The only required key is `notebook` (i.e. if you use `.otter` file it must specify a value for `notebook`).

```jsonc
{
    "notebook": "",            // the notebook filename
    "endpoint": null,          // the Otter Service endpoint
    "assignment_id": "",       // assignment ID in the Otter Service database
    "class_id": "",            // class ID in the Otter Service database
    "auth": "google",          // the auth type for your Otter Service deployment
    "save_environment": false, // whether to serialize the environment in the log during checks
    "ignore_modules": [],      // a list of modules whose functions to ignore during serialization
    "variables": {}            // a mapping of variable names -> types to resitrct during serialization
}
```

## Configuring Otter Service

The main use of a `.otter` file is to configure submission to an [Otter Service deployment](otter_service.md). This requires that the `endpoint`, `assignment_id`, and `class_id` keys be specified. The optional `auth` key corresponds to the name of the service's auth provider (defaulting to `google`). With these specified, students will be able to use `Notebook.submit` to send their notebook submission to the Otter Service deployment so that it can be graded. An example of this use would be:

```json
{
    "notebook": "hw00.ipynb",
    "endpoint": "http://some.url",
    "assignment_id": "hw00",
    "class_id": "some_class",
    "auth": "google"
}
```

More information can be found in [Grading on a Deployable Service](otter_service.md)

## Configuring the Serialization of Environments

If you are using logs to grade assignemtns from serialized environments, the `save_environment` key must be set to `true`. Any module names in the `ignore_modules` list will have their functions ignored during serialization. If `variables` is specified, it should be a dictionary mapping variables names to fully-qualified types; variables will only be serialized if they are present as keys in this dictionary and their type matches the specified type. An example of this use would be:

```json
{
    "notebook": "hw00.ipynb",
    "save_environment": true,
    "variables": {
        "df": "pandas.core.frame.DataFrame",
        "fn": "builtins.function",
        "arr": "numpy.ndarray"
    }
}
```

The function `otter.utils.get_variable_type` when called on an object will return this fully-qualified type string.

```python
>>> from otter.utils import get_variable_type
>>> import numpy as np
>>> import pandas as pd
>>> get_variable_type(np.array([]))
'numpy.ndarray'
>>> get_variable_type(pd.DataFrame())
'pandas.core.frame.DataFrame'
>>> fn = lambda x: x
>>> get_variable_type(fn)
'builtins.function'
```

More information about grading from serialized environments can be found in [Logging](logging.md).
