# Changelog

**v2.1.2:**

* Added `Notebook.export` format support for Otter Grade
* Fixed tutorial in documentation
* Added `force_save` argument to `otter.Notebook.export` to make notebook force-save optional

**v2.1.1:**

* Fixed `UnboundLocalError` with log in `otter.run.run_autograder.run_autograder`

**v2.1.0:**

* Added `nb_conda_kernels` to template environment.yml
* Fixed duplicate token calls when using Otter Assign to call Otter Generate
* Updated grading image to Miniconda 4.9.2 with Python 3.8
* Changed Otter conda environment name to `otter-env`
* Added `warnings` import to `otter.check.notebook`

**v2.0.8:**

* Passed plugin collection while running tests in Otter Assign
* Fixed adding directories in `files` with Otter Generate

**v2.0.7:**

* Changed `scripts` to `entry_points` in setup.py for Windows compatibility and removed `bin/otter`
* Added `otter.check.utils.save_notebook` for autosaving notebooks on export calls
* Updated OK format to allow `points` key to be a list of length equal to the number of test cases

**v2.0.6:**

* Fixed requirements not found error for R notebooks in Otter Assign
* Removed use of `re` in overriding `Notebook` test directory override in `otter.execute.execute_notebook` by adding `otter.Notebook._test_dir_override`

**v2.0.5:**

* Fixed `NoneType` issue in `PluginCollection.generate_report`

**v2.0.4:**

* Added ignoreable lines in Otter Assign
* Added error handling for log deserialization per [#190](https://github.com/ucbds-infra/otter-grader/issues/190)
* Added plugin data storage per [#191](https://github.com/ucbds-infra/otter-grader/issues/191)

**v2.0.3:**

* Fixed positional arg count in ``otter.plugins.builtin.GoogleSheetsGradeOverride``
* Fixed working directory in ``otter.plugins.builtin.GoogleSheetsGradeOverride`` during Otter Assign

**v2.0.2:**

* Fixed [#185](https://github.com/ucbds-infra/otter-grader/issues/185)

**v2.0.1:**

* Added the `each` key to `points` in question metadata for Otter Assign

**v2.0.0:**

* Changed granularity of results to be test case-by-test case rather than by file
* Added ability to list requirements directly in assignment metadata w/out requirements.txt file
* Unified assignment grading workflow and converted local grading to container-per-submission
* Exposed grading internals for non-containerized grading via `otter run` and `otter.api`
* Added plugins for altering grades and execution, incl. built-in plugins
* Added ignorable cells to Otter Assign
* Added `autograder_files` configuration for Otter Assign
* Added passdown of assignment configurations to Otter Generate from Otter Assign
* Fixed whitespace bug in Assign solution parsing
* Resolved conflicts with `nbconvert>=6.0.0`, removed version pin
* Added `otter.assign.utils.patch_copytree` as a patch for `shutil.copytee` on WSL
* Refactored Otter Generate to use `zipfile` to generate zips
* Refactored CLI to allow creation of programmatic API
* Changed `otter generate autograder` to `otter generate`
* Removed `otter generate token` as all interaction with `otter.generate.token.APIClient` can be handled elsewhere
* Added intercell seeding for R Jupyter Notebooks
* Added `ValueError` on unexpected config in `otter.assign.assignment.Assignment`
* Added `--username`, `--password` flags to Otter Assign and Otter Generate
* Added support for Python files
* Removed `FutureWarning` for deprecated global `hidden` key of OK tests
* Add missing file specifier in environment template

**v1.1.6:**

* Fixed `ZeroDivisionError` when an assignment has 0 points total

**v1.1.5:**

* Fixed error in parsing requirements when using Otter Grade

**v1.1.4:**

* Fixed `KeyError` when kernelspec unparsable from notebook in Otter Assign

**v1.1.3:** 

* Changed Rmd code prompt to `NULL # YOUR CODE HERE` for assignment statements and `# YOUR CODE HERE` for whole-line and block removal

**v1.1.2:**

* Made requirements specification always throw an error if a user-specified path is not found
* Pinned `nbconvert<6.0.0` as a temporary measure due to new templating issues in that release

**v1.1.1:**

* Fixed handling variable name collisions with already-tested test files
* Added `--no-pdfs` flag to Otter Assign

**v1.1.0:**

* Moved Gradescope grading to inside conda env within container due to change in Gradescope's grading image
* Added ability to specify additional tests to be run in cell metadata without need of explicit `Notebook.check` cells

**v1.0.1:**

* Fixed bug with specification of overwriting requirements in Otter Generate

**v1.0.0:**

* Changed structure of CLI into six main commands: `otter assign`, `otter check`, `otter export`, `otter generate`, `otter grade`, and `otter service`
* Added R autograding integrations with autograding package [ottr](https://github.com/ucbds-infra/ottr)
* Added Otter Assign, a forked version of [jassign](https://github.com/okpy/jassign) that works with Otter
* Added Otter Export, a forked version of [nb2pdf](https://github.com/ucbds-infra/nb2pdf) and [gsExport](https://github.com/dibyaghosh/gsExport) for generating PDFs of notebooks
* Added Otter Service, a deployable grading service that students can POST their submissions to
* Added logging to `otter.Notebook` and Otter Check, incl. environment serialization for grading
* Changed filenames inside the package so that names match commands (e.g. `otter/cli.py` is now `otter/grade.py`)
* Added intercell seeding
* Moved all argparse calls into `otter.argparser` and the logic for routing Otter commands to `otter.run`
* Made several fixes to `otter check`, incl. ability to grade notebooks with it
* `otter generate` and `otter grade` now remove tmp directories on failure
* Fixed `otter.ok_parser.CheckCallWrapper` finding and patching instances of `otter.Notebook`
* Changed behavior of hidden test cases to use individual case `"hidden"` key instead of global `"hidden"` key
* Made use of metadata files in `otter grade` optional
* Added `otter_ignore` cell tag to flag a cell to be ignored during notebook execution

**v0.4.8:**

* added import of `IPython.display.display` to `otter/grade.py`
* patched Gradescope metadata parser for group submissions

**v0.4.7:**

* fix relative import issue on Gradescope (again, *sigh*)

**v0.4.6:** re-release of v0.4.5

**v0.4.5:**

* added missing patch of `otter.Notebook.export` in `otter/grade.py`
* added `__version__` global in `otter/__init__.py`
* fixed relative import issue when running on Gradescope
* fixed not finding/rerunning tests on Gradescope with `otter.Notebook.check`

**v0.4.4:**

* fixed template escape bug in `otter/gs_generator.py`

**v0.4.3:**

* fixed dead link in `docs/gradescope.md`
* updated to Python 3.7 in setup.sh for Gradescope
* made `otter` and `otter gen` CLIs find `./requirements.txt` automatically if it exists
* fix bug where GS generator fails if no `-r` flag specified
