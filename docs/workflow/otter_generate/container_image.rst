.. _workflow_otter_generate_container_image:

Grading Container Image
=======================

When you use Otter Generate to create the configuration zip file for Gradescope, Otter includes the 
following software and packages for installation. The zip archive, when unzipped, has the following 
contents:

.. code-block::

    autograder
    ├── environment.yml
    ├── files/
    ├── otter_config.json
    ├── requirements.r
    ├── run_autograder
    ├── run_otter.py
    ├── setup.sh
    └── tests/

Note that for pure-Python assignments, ``requirements.r`` is not included and all of the 
R-pertinent portions of ``setup.sh`` are removed. Below are descriptions of each of the items 
listed above and the Jinja2 templates used to create them (if applicable).


``setup.sh``
------------

This file, required by Gradescope, performs the installation of necessary software for the 
autograder to run.

The template for Python assignments is:

.. literalinclude:: ../../_static/python_setup.sh
    :language: shell

And the template for R assignments is:

.. literalinclude:: ../../_static/r_setup.sh
    :language: shell

Note that the line ``mamba run -n otter-env Rscript /autograder/source/requirements.r`` is only
included if you have provided an :ref:`R requirements file 
<otter_generate_container_image_requirements_r>`.


``environment.yml``
-------------------

This file specifies the conda environment that Otter creates in ``setup.sh``. By default, it uses
Python 3.9, but this can be changed using the ``--python-version`` flag to Otter Generate.

.. literalinclude:: ../../_static/grading-environment.yml
    :language: yaml

If you're grading a Python assignment, any dependencies in your ``requirements.txt`` will be added
to the ``pip`` list in this file. If you pass ``--overwrite-requirements``, your
``requirements.txt`` contents will be in the ``pip`` list instead of what's above.

If you're grading an R assignment, the ``environment.yml`` has additional depdencies:

.. literalinclude:: ../../_static/grading-environment-r.yml
    :language: yaml


.. _otter_generate_container_image_requirements_r:

``requirements.r``
------------------

If you're grading an R assignment, this file will be included if you specify it in the
``--requirements`` argument, and is just a copy of the file you provide. It should use functions
like ``install.packages`` to install any additional dependencies your assignment requires.
(Alternatively, if the depdendencies are available via conda, you can specify them in an
``environment.yml``.)


``run_autograder``
------------------

This is the file that Gradescope uses to actually run the autograder when a student submits. Otter 
provides this file as an executable that activates the conda environment and then calls 
``/autograder/source/run_otter.py``:

.. literalinclude:: ../../../otter/generate/templates/common/run_autograder
    :language: shell


``run_otter.py``
-----------------

This file contains the logic to start the grading process by importing and running 
``otter.run.run_autograder.main``:

.. literalinclude:: ../../../otter/generate/templates/common/run_otter.py
    :language: python


``otter_config.json``
---------------------

This file contains any user configurations for grading. It has no template but is populated with the 
any non-default values you specify for these configurations. When debugging grading via SSH 
on Gradescope, a helpful tip is to set the ``debug`` key of this JSON file to ``true``; this will 
stop the autograding from ignoring errors when running students' code, and can be helpful in 
debugging specific submission issues.


``tests``
---------

This is a directory containing the test files that you provide. All ``.py`` (or ``.R``) files in the 
tests directory path that you provide are copied into this directory and are made available to 
submissions when the autograder runs.


``files``
---------

This directory, not present in all autograder zip files, contains any support files that you provide 
to be made available to submissions.
