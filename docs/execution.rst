Submission Execution
====================

This section of the documentation describes the process by which submissions are executed in the 
autograder. Regardless of the method by which Otter is used, the autograding internals are all the 
same, although the execution differs slightly based on the file type of the submission.


Python
------

All Python submissions, regardless of type, are converted to notebooks and graded with nbformat's
``ExecutePreprocessor``. For Python scripts, they are converted by creating a notebook with a
single code cell that contains the script's contents.

The notebooks are executed as follows:

#. The ``before_execution`` :ref:`plugin <plugins>` event is run.
#. Cells tagged with ``otter_ignore`` or with ``otter[ignore]`` set to ``true`` in the metadata are
   removed from the notebook.
#. (If grading from an Otter log) all lines of code which are not import statements are removed from
   the submission and replaced with code to unpack the serialized environments from the log.
#. Additional checks indicated in the cell metadata (``otter[tests]``) are added those cells.
#. (If intercell seeding is being used) a cell importing ``numpy`` and ``random`` is added to the
   top of the notebook and each code cell is prepended with the seeding code.
#. The current working directory is added to ``sys.path``.
#. Cells to initialize Otter and export grading results are added at the beginning and end of the
   notebook, respectively.
#. The notebook is executed with the ``ExecutePreprocessor``. If running in debug mode, errors are
   not ignored.
#. The results exported by Otter from the notebook are loaded.
#. The ``after_grading`` :ref:`plugin <plugins>` event is run.
