# Changelog

**v6.0.4:**

* Added `jupyter_server` to grading environment to allow for installation of `nb_conda_kernels`

**v6.0.3:**

* Fixed `TypeError` thrown by Otter Run

**v6.0.2:**

* Fixed dependency issues when installing on JupyterLite per [#875](https://github.com/ucbds-infra/otter-grader/issues/875)

**v6.0.1:**

* Updated dependency specifications to support any new minor version within the matching major version
* Fixed `SyntaxError` thrown by `gmail_oauth2` binary

**v6.0.0:**

* Switched to [poetry](https://python-poetry.org/) for packaging
* Removed compatibility patches for nbconvert < 6 per [#777](https://github.com/ucbds-infra/otter-grader/issues/777)
* Updated Otter Export to throw an error if nbconvert<6.0.0 is found
* Converted Otter Export's PDF via HTML exporter to use nbconvert's WebPDF exporter per [#781](https://github.com/ucbds-infra/otter-grader/issues/781)
* Removed pdfkit from dependencies
* Added ability to export PDFs via HTML in grading containers per [#782](https://github.com/ucbds-infra/otter-grader/issues/782)
* Set default Python version for grading images to 3.12
* Remove support for Python versions < 3.9 per [#668](https://github.com/ucbds-infra/otter-grader/issues/668)
* Removed `setuptools` and `pkg_resources` dependencies
* Remove dependencies not strictly required by Otter in the grading environment per [#739](https://github.com/ucbds-infra/otter-grader/issues/739)
* Handle empty assignment configs in Otter Assign per [#795](https://github.com/ucbds-infra/otter-grader/issues/795)
* Removed `Notebook` `colab` and `jupyterlite` arguments, switching to always determining the interpreter automatically
* Made `dill` a required dependency
* Removed `variables` key of assignment config in favor of `generate.serialized_variables` in Otter Assign per [#628](https://github.com/ucbds-infra/otter-grader/issues/628)
* Update Otter Assign to add cell metadata so that questions with no check cell have their tests run after the last solution cell per [#798](https://github.com/ucbds-infra/otter-grader/issues/798)
* Updated Otter Assign to strip type annotations from generated test code per [#796](https://github.com/ucbds-infra/otter-grader/issues/796)
* Updated Otter Grade Docker image to create an empty `submission_metadata.json` file in the grading image to prevent plugins from erroring per [#811](https://github.com/ucbds-infra/otter-grader/issues/811)
* Added ability to monitor grading progress to Otter Grade per [#827](https://github.com/ucbds-infra/otter-grader/issues/827)
* Added handling of student-created files with the `student_files` configuration in Otter Assign per [#737](https://github.com/ucbds-infra/otter-grader/issues/737)
* Updated Otter Assign to add a cell to install Otter at the top of Colab notebooks per [#861](https://github.com/ucbds-infra/otter-grader/issues/861)
* Added the ability to ignore the `.OTTER_LOG` file to `Notebook.export` and Otter Assign per [#857](https://github.com/ucbds-infra/otter-grader/issues/857)
* Fixed OK-test support for the `all_or_nothing` config per [#751](https://github.com/ucbds-infra/otter-grader/issues/751)
* Added exception-based test support for the `all_or_nothing` config per [#751](https://github.com/ucbds-infra/otter-grader/issues/751)
* Added Otter Assign support for the `all_or_nothing` config per [#751](https://github.com/ucbds-infra/otter-grader/issues/751)
* Updated Otter Assign to only allow a function definition and statement to call the test function in exception-based test cells and automatically ignore the latter statement instead of requiring an explicit `# IGNORE` comment per [#516](https://github.com/ucbds-infra/otter-grader/issues/516)
* Added additional package versions to the output of `otter --version` per [#843](https://github.com/ucbds-infra/otter-grader/issues/843)
* Fixed bug in converting test cells containing indented functions to doctests in Otter Assign per [#840](https://github.com/ucbds-infra/otter-grader/issues/840)

**v5.7.1:**

* Removed testing code unintentioanlly committed in v5.7.0 per [#849](https://github.com/ucbds-infra/otter-grader/issues/849)

**v5.7.0:**

* Switch grading image from Mambaforge to Miniforge due to the [sunestting of Mambaforge](https://conda-forge.org/news/2024/07/29/sunsetting-mambaforge/) per [#846](https://github.com/ucbds-infra/otter-grader/issues/846)

**v5.6.0:**

* Updated Otter Grade to write grading summary for each notebook per [#814](https://github.com/ucbds-infra/otter-grader/issues/814)
* Updated Otter Grade CSV to indicate which notebooks timeout per [#813](https://github.com/ucbds-infra/otter-grader/issues/813)
* Updated Otter Grade CSV to include the number of points per question in the first row
* Updated Otter Grade CSV to include total points column
* Updated Otter Grade CSV to round percentages to four decimal places
* Updated Otter Grade CSV output switched from labeling submissions by file path to notebook name and is now sorted by notebook name per [#738](https://github.com/ucbds-infra/otter-grader/issues/738)
* Added backwards compatibility to Otter Grade for autograder configuration zip files generated in previous major versions of Otter-Grader
* Add `gcc_linux-64` and `gxx_linux-64` to R grading image dependencies per [#819](https://github.com/ucbds-infra/otter-grader/issues/819)
* Fixed a bug where the loop variable used in Otter's generated grading code overwrote variables defined by the notebook per [#817](https://github.com/ucbds-infra/otter-grader/issues/817)
* Add `--pickle-results` option to Otter Run to output the results pickle file per [#818](https://github.com/ucbds-infra/otter-grader/issues/818)
* Added `setuptools` to Otter's required dependencies per [#823](https://github.com/ucbds-infra/otter-grader/issues/823)

**v5.5.0:**

* Suppress all warnings when running `otter.check.validate_export` as a module per [#735](https://github.com/ucbds-infra/otter-grader/issues/735)
* Updated default version of `ottr` to v1.5.0
* Added a way to exclude Conda's defaults channel from autograder `environment.yml` files in Otter Assign and Otter Generate per [#778](https://github.com/ucbds-infra/otter-grader/issues/778)

**v5.4.1:**

* Fixed import of the `LatexFailed` error for `nbconvert` 7

**v5.4.0:**

* Updated submission runners to export and submit the PDF and then remove all copies of the API token before executing the submission to ensure that student code can't gain access to the token
* Updated Otter Run to skip PDF export and upload in debug mode

**v5.3.0:**

* Updated Otter Assign to throw a `ValueError` when invalid Python code is encountered in test cells per [#756](https://github.com/ucbds-infra/otter-grader/issues/756)
* Fixed an error causing intercell seeding code to be added to cells using cell magic commands which caused syntax errors per [#754](https://github.com/ucbds-infra/otter-grader/issues/754)
* Add support for submitting the PDF uploaded in a submission for manual grading instead of generating a new one per [#764](https://github.com/ucbds-infra/otter-grader/issues/764)
* Validate that a course ID and assignment ID were provided before attempting PDF upload
* Upgrade and pin pandoc to v3.1.11.1 in grading images per [#709](https://github.com/ucbds-infra/otter-grader/issues/709)

**v5.2.3:**

* Fixed the no PDF acknowledgement feature to handle when PDF exports throw an error instead of failing silently

**v5.2.2:**

* Fixed an `AttributeError` when using `Notebook.check_all` per [#746](https://github.com/ucbds-infra/otter-grader/issues/746)

**v5.2.1:**

* Fixed an `AttributeError` when using OK tests from notebook metadata per [#743](https://github.com/ucbds-infra/otter-grader/issues/743)

**v5.2.0:**

* Migrate installation of `ottr` from `setup.sh` to `environment.yml` with the [`r-ottr` conda-forge recipe](https://anaconda.org/conda-forge/r-ottr)
* Updated Otter Assign to allow multiline statements in test cases for Python 3.9+ per [#590](https://github.com/ucbds-infra/otter-grader/issues/590)
* Added `otter_include` tag to allow inclusion of tagged markdown cells within the solution block into the student notebook per [#730](https://github.com/ucbds-infra/otter-grader/issues/730)
* Removed dependency on `nbconvert` during import so that Otter can be imported on Jupyterlite per [#736](https://github.com/ucbds-infra/otter-grader/issues/736)

**v5.1.4:**

* Prevented the `Notebook` class from attempting to resolve the notebook path when in grading mode
* Gracefully handle a failure in reading the results pickle file by returning results indicating that such a failure has occurred per [#723](https://github.com/ucbds-infra/otter-grader/issues/723)
* Use `tempfile.mkstemp` instead of `tempfile.NamedTemporaryFile` for the results pickle file used during notebook execution per [#723#issuecomment-1710689536](https://github.com/ucbds-infra/otter-grader/issues/723#issuecomment-1710689536)

**v5.1.3:**

* Fixed bug in submission zip download link per [#719](https://github.com/ucbds-infra/otter-grader/issues/719)

**v5.1.2:**

* Enabled the use of custom Jupyter kernels by enforcing the use of the `python3` kernel inside Otter grading containers per [#706](https://github.com/ucbds-infra/otter-grader/issues/706)
* Fixed a bug that was preventing Otter from exiting when an error was thrown during notebook execution caused by the log capturing solution per [#707](https://github.com/ucbds-infra/otter-grader/issues/707)
* Updated PDF upload logic to surface error statuses returned by the Gradescope API

**v5.1.1:**

* Fixed a bug in attempting to read the users from the submission metadata when validating the autograder notebook in Otter Assign per [#695](https://github.com/ucbds-infra/otter-grader/issues/695)
* Added `__getstate__` to `test_case` to fix pickling bug for exception style tests per [#696](https://github.com/ucbds-infra/otter-grader/issues/696)
* Added back remove cell ID patch to Otter Assign for notebooks with nbformat version < 4.5 per [#701](https://github.com/ucbds-infra/otter-grader/issues/701)

**v5.1.0:**

* Removed patch that strips cell IDs from notebooks in Otter Assign per [#677](https://github.com/ucbds-infra/otter-grader/issues/677)
* Added notebook force-save to R notebook assignments per [#474](https://github.com/ucbds-infra/otter-grader/issues/474)
* Updated default version of `ottr` to v1.4.0
* Added a configuration to require students to acknowledge when a PDF of their notebook cannot be generated when using `Notebook.export` before exporting the zip file per [#599](https://github.com/ucbds-infra/otter-grader/issues/599)
* Added a simple TCP socket server for receiving Otter's logs from the executed notebook to re-enable question logging during Otter Assign per [#589](https://github.com/ucbds-infra/otter-grader/issues/589)
* Fixed recursive inclusion of files when a directory is in the list passed to the `files` argument of `Notebook.export` per [#620](https://github.com/ucbds-infra/otter-grader/issues/620)
* Fixed the grader export cell failing due to warnings about frozen modules per [#686](https://github.com/ucbds-infra/otter-grader/issues/686)

**v5.0.2:**

* Fixed local submission zip checking with `otter.Notebook` per [#678](https://github.com/ucbds-infra/otter-grader/issues/678)

**v5.0.1:**

* Added `nbconvert` as a required dependency for non-WASM environments

**v5.0.0:**

* Converted all dependency management in the autograder configuration zip file to Conda per [#501](https://github.com/ucbds-infra/otter-grader/issues/501)
* Removed deprecated Otter Assign format v0
* Disabled editing for question prompt cells in the notebooks generated by Otter Assign per [#431](https://github.com/ucbds-infra/otter-grader/issues/431)
* Removed `ucbdsinfra/otter-grader` Docker image and made default image for Otter Grade `ubuntu:22.04` per [#534](https://github.com/ucbds-infra/otter-grader/issues/534)
* Make `xeCJK` opt-in behavior for exporting notebooks via LaTeX per [#548](https://github.com/ucbds-infra/otter-grader/issues/548)
* Convert from use of deprecated `PyPDF2` package to `pypdf`
* Add configuration to submit blank PDF to manual-grading Gradescope assignment if PDF generation fails per [#551](https://github.com/ucbds-infra/otter-grader/issues/551)
* Removed the `after_execution` event from the plugin lifecycle
* Updated execution internals to use `nbconvert.preprocessors.ExecutePreprocessor` instead of the `exec` function to execute submissions per [#604](https://github.com/ucbds-infra/otter-grader/issues/604)
* Deprecated the `variables` key of the assignment config in favor of `generate.serialized_variables`
* Enabled Otter Generate for all assignments created with Otter Assign
* Updated Otter Assign to use Otter Run to validate that all tests in the assignment pass, allowing tests to be run for R assignments as well as Python, per [#427](https://github.com/ucbds-infra/otter-grader/issues/427)
* Allow Markdown cells to be used instead of raw cells for Otter Assign per [#592](https://github.com/ucbds-infra/otter-grader/issues/592)
* Use Otter Grade CLI flags to update `otter_config.json` values in the grading container per [#395](https://github.com/ucbds-infra/otter-grader/issues/395)
* Removed `linux/amd64` platform specification for Docker images in Otter Grade
* Updated Otter Assign to normalize notebooks before writing them with `nbformat.validator.normalize` per [#658](https://github.com/ucbds-infra/otter-grader/issues/658)
* Added summary of assignment questions to Otter Assign logging per [#564](https://github.com/ucbds-infra/otter-grader/issues/564)
* Converted to Mamba from Conda for package management in grading containers per [#660](https://github.com/ucbds-infra/otter-grader/issues/660)
* Upgraded default Python version in grading containers from 3.7 to 3.9

**v4.4.1:**

* Update Otter Grade to close file handles before copying files out of Docker containers to fix bug on Windows

**v4.4.0:**

* Moved `google-api-python-client`, `google-auth-oauthlib`, and `six` from required installation dependencies to test dependencies to allow installation of Otter with Mamba per [#633](https://github.com/ucbds-infra/otter-grader/issues/633)
* Added question name to point value validation error messages per [#586](https://github.com/ucbds-infra/otter-grader/issues/586)
* Fixed bug in copying plugin configurations from assignment config to `otter_config.json` in Otter Assign

**v4.3.4:**

* Set tests directory path when calling `ottr::run_autograder` from Otter Run

**v.4.3.3:**

* Fix Otter Assign slowdown due to poor-performance regex per [#634](https://github.com/ucbds-infra/otter-grader/issues/634)

**v4.3.2:**

* Fix bug in determining whether the active interpreter is Jupyterlite in `otter.Notebook` per [#511](https://github.com/ucbds-infra/otter-grader/issues/511#issuecomment-1500964637)
* Fix bug in verifying scores against logs that caused all verifications to throw an error if hidden tests were ignored

**v4.3.1:**

* Change `sklearn` to `scikit-learn` in requirements files generated by Otter Generate

**4.3.0:**

* Support dictionary and tuple assignments in solution substitution in Otter Assign per [#587](https://github.com/ucbds-infra/otter-grader/issues/587)
* Add the `pdf` argument to `ottr::export` in R assignments created with Otter Assign per [#440](https://github.com/ucbds-infra/otter-grader/issues/440)

**v4.2.1:**

* Update Otter Grade image tag when the base image changes per [#583](https://github.com/ucbds-infra/otter-grader/issues/583)
* Make gspread an optional dependency per [#577](https://github.com/ucbds-infra/otter-grader/issues/577)

**v4.2.0:**

* Added configuration files for Otter Assign per [#565](https://github.com/ucbds-infra/otter-grader/issues/565)
* Fixed log execution bug from Slack as described in [#571](https://github.com/ucbds-infra/otter-grader/pull/571)

**v4.1.2:**

* Added `ipython` to `install_requires`

**v4.1.1:**

* Added `MANIFEST.in`

**v4.1.0:**

* Display emojis with test results to more clearly show which tests pass and which fail, as per [#533](https://github.com/ucbds-infra/otter-grader/pull/533).
* Allow users to specify a Python version in Otter Generate and Otter Assign
* Round `results.json` point values to 5 decimal places per [#538](https://github.com/ucbds-infra/otter-grader/issues/538)
* Optionally display PDF generation/submission failures to students via `results.json` per [#494](https://github.com/ucbds-infra/otter-grader/issues/494)
* Added the `force_public_test_summary` key to the autograder config per [#539](https://github.com/ucbds-infra/otter-grader/issues/539)
* Made the "Public Tests" section on Gradescope appear as failing when not all public tests passed per [#539](https://github.com/ucbds-infra/otter-grader/issues/539)

**v4.0.2:**

* Close temporary file handle before removal when checking tests in `otter.Notebook.export`
* Fixed bug caused by unspecified encoding in Windows JSON loads per [#524](https://github.com/ucbds-infra/otter-grader/issues/524)
* Updated autograder zip `setup.sh` file and `r-base` version per [#514](https://github.com/ucbds-infra/otter-grader/issues/514)
* Fix point value filtering for student tests in Otter Assign per [#503](https://github.com/ucbds-infra/otter-grader/issues/503)

**v4.0.1:**

* Fix Otter Grade Dockerfile per [#517](https://github.com/ucbds-infra/otter-grader/issues/517)
* Fix display of Public Tests output on Gradescope due to new output format
* Updated Otter Export to only import the HTML exporter and its dependencies when an HTML export is indicated per [#520](https://github.com/ucbds-infra/otter-grader/issues/520)

**v4.0.0:**

* Added a new test file format based on raising exceptions per [#95](https://github.com/ucbds-infra/otter-grader/issues/95)
* Refactored execution internals to remove mocks and AST parsing
* Added use of `tempfile` to store the executed source for compilation per [#229](https://github.com/ucbds-infra/otter-grader/issues/229)
* Added use of `wrapt` for `otter.Notebook` method decorators
* Set `export_cell: run_tests: true` and `check_all_cell: false` as new defaults for Otter Assign per [#378](https://github.com/ucbds-infra/otter-grader/issues/378)
* Made the v1 format of Otter Assign the default and added the `--v0` flag to the CLI
* Converted logging in some of Otter's tooling from `print` statements to the `logging` library, and added verbosity flags to each command
* Updated containerized grading to better handle grading single files
* Made Otter compatible with Jupyterlite per [#458](https://github.com/ucbds-infra/otter-grader/issues/458)
* Added Otter Assign R Markdown format v1 per [#491](https://github.com/ucbds-infra/otter-grader/issues/491)
* Refactored Otter Assign internals per [#491](https://github.com/ucbds-infra/otter-grader/issues/491)
* Converted user-supplied configuration management and documentation to `fica` per [#485](https://github.com/ucbds-infra/otter-grader/issues/485)
* Added assignment names to Otter Assign and Otter Generate that can be verified by Otter Run to prevent students from submitting to the wrong autograder per [#497](https://github.com/ucbds-infra/otter-grader/issues/497)
* Set the default version of `ottr` to v1.2.0

**v3.3.0:**

* Made `otter.check.utils.save_notebook` compatible with JupyterLab and RetroLab per [#448](https://github.com/ucbds-infra/otter-grader/issues/448)
* Add `libmagick++-dev` to Gradescope R autograding image

**v3.2.1:**

* Display instructor-specified messages ahead of doctest messages per [#441](https://github.com/ucbds-infra/otter-grader/issues/441)
* Round point values for display to 5 decimal places in Otter Assign per [#457](https://github.com/ucbds-infra/otter-grader/issues/457)

**v3.2.0:**

* Changed Otter Generate to accept the path to the zip file to write as the output argument rather than a directory in which to write a file called `autograder.zip`
* Changed the file name of the zip file generated by Otter Assign to include the master notebook basename and a timestamp per [#401](https://github.com/ucbds-infra/otter-grader/issues/401)
* Made `xeCJK` in Otter Export's LaTeX templates optional per [#411](https://github.com/ucbds-infra/otter-grader/issues/411)
* Removed concise error messages and debug mode from Otter Export, instead opting to always display the full error message, per [#407](https://github.com/ucbds-infra/otter-grader/issues/407)
* Upgraded to Ottr v1.1.3
* Set the default for the `--ext` option for Otter Grade to `ipynb` per [#418](https://github.com/ucbds-infra/otter-grader/pull/418)
* Fixed the display of success messages when all tests cases pass per [#425](https://github.com/ucbds-infra/otter-grader/issues/425)
* Added an error when the expected notebook file does not exist in `otter.Notebook` per [#433](https://github.com/ucbds-infra/otter-grader/issues/433)
* Allow unset conda `channel_priority` in R setup.sh files per [#430](https://github.com/ucbds-infra/otter-grader/issues/430)
* Reset all cell execution counts in Assign student notebook per [#422](https://github.com/ucbds-infra/otter-grader/issues/422)

**v3.1.4:**

* Added the question name to the `otter.assign.utils.AssignNotebookFormatException` per [#398](https://github.com/ucbds-infra/otter-grader/issues/398)
* Switched from manual install of the fandol font in grading images to installing the `texlive-lang-chinese` package
* Allowed submission zip to be exported even when PDF generation fails per [#403](https://github.com/ucbds-infra/otter-grader/issues/403)
* Fixed bug in Otter Assign that fails when a notebook has no tests

**v3.1.3:**

* Fixed [#389](https://github.com/ucbds-infra/otter-grader/issues/389) by closing file handles in Otter Grade before removing them
* Fixed R image builds by setting Conda `channel_priority` to `strict` in R `setup.sh` files per [#386](https://github.com/ucbds-infra/otter-grader/issues/386)
* Fix loading docker images after building
* Added the `--ext` option to Otter Grade per [#386](https://github.com/ucbds-infra/otter-grader/issues/386)

**v3.1.2:**

* Specify UTF-8 encoding in all `open` calls used for reading JSON for Windows compatibility per [#380](https://github.com/ucbds-infra/otter-grader/issues/380)
* Fixed incorrect prompt substitution in R notebooks and Rmd assignments

**v3.1.1:**

* Added `libgomp` to R `environment.yml`

**v3.1.0:**

* Added a tool to convert Assign v0-formatted notebooks to v1 format
* Added `xeCJK` to the LaTeX exporter template and Docker images
* Added PDF generation and submission in R per [#302](https://github.com/ucbds-infra/otter-grader/issues/302)
* Updated intercell seeding in R per [#302](https://github.com/ucbds-infra/otter-grader/issues/302)
* Fixed bug in test case point values for Assign R assignments per [#360](https://github.com/ucbds-infra/otter-grader/issues/360)
* Enabled `solutions_pdf` and `template_pdf` in Assign R assignments per [#364](https://github.com/ucbds-infra/otter-grader/issues/364)
* Added options to limit execution time of grading and permit network access
* Refactored R submission reformatting per [#369](https://github.com/ucbds-infra/otter-grader/issues/369)
* Added export cells for R notebooks in Otter Assign per [#369](https://github.com/ucbds-infra/otter-grader/issues/369)
* Updated the default version of Ottr to v1.1.1
* Changed prompts in R notebooks to match Rmd documents
* Added filtering of notebook cells with syntax errors during R notebook execution
* Enured that "empty" tokens are ignored in Otter Generate per [#361](https://github.com/ucbds-infra/otter-grader/issues/361)
* Prevented save text when `export_cell: force_save: true` is specified in Otter Assign assignment metadata per [#332](https://github.com/ucbds-infra/otter-grader/issues/332)

**v3.0.6:** re-release of v3.0.5

**v3.0.5:**

* Refactored Otter's execution internals
* Added intercell seeding via seed variables per [#346](https://github.com/ucbds-infra/otter-grader/issues/346)
* Made Otter Run compatible with ZIP submissions
* Fixed argument bug in Otter Run per [#349](https://github.com/ucbds-infra/otter-grader/issues/349)

**v3.0.4:**

* Fixed bug in Otter Assign format v1 for closing exports when the last question is manually-graded
* Removed cell IDs in Otter Assign output notebooks per [#340](https://github.com/ucbds-infra/otter-grader/issues/340)
* Changed submission zip download link to use the HTML `download` attribute per [#339](https://github.com/ucbds-infra/otter-grader/issues/339)

**v3.0.3:**

* Fix some minor bugs using docker for grading
* Added support for test config blocks in R assignments
* Fixed use of `autograder_files` in Otter Assign
* Removed the `generate: pdfs` key from Otter Assign assignment configurations
* Converted from Docker-py to Python on Whales for containerized grading

**v3.0.2:**

* Made `otter.Notebook.check_all` compatible with metadata tests
* Refactored logging in `otter.Notebook`
* Fixed parsing of Windows newlines in Otter Assign

**v3.0.1:**

* Updated the default version of Ottr to v1.0.0
* Ensured that metadata tests for R notebooks are disabled

**v3.0.0:**

* Added Colab support to `otter.Notebook` by disabling methods that require a notebook path and ensuring that a tests directory is present
* Added Otter Assign format v1
* Added `FutureWarning` for Otter Assign format v0
* Default-disabled separate test files in Otter Assign v1 format
* Fixed bug in Otter Assign for R causing point values in test files not to render
* Added the `check_cell` key to question metadata in Otter Assign
* Fixed installation of `stringi` in Gradescope R build per [#259](https://github.com/ucbds-infra/otter-grader/issues/259)
* Added support for Ottr v1.0.0.b0
* Converted CLI to `click` from `argparse`
* Converted documentation source from Markdown to RST, removing use of `recommonmark`
* Added token argument to Otter Generate and Otter Assign
* Implemented submission zip validation against local test cases in `otter.Notebook`
* Removed metadata files for Otter Grade
* Added flags for disabling file auto-inclusion in Otter Generate

**v2.2.7:**

* Added student-visible error reporting in Gradescope results

**v2.2.6:**

* Updated Otter Grade Dockerfile to simplify build process
* Updated Otter Grade container management workflow
* Updated `setup.sh` templates to reflect the new Dockerfile changes
* Changed the display of failed test results in Otter Assign validation
* Made `rpy2` an optional depenency

**v2.2.5:**

* Upgraded to Miniconda 4.10.3 in grading images
* Fixed [#272](https://github.com/ucbds-infra/otter-grader/issues/272)

**v2.2.4:**

* Fixed total score printout for the use of the `points_possible` configuration

**v2.2.3:**

* Added `NotebookMetadataTestFile` for reading tests from Jupyter Notebook metadata
* Added optional storage of tests in notebook metadata for Otter Assign (default-off until v3)


* Removed deprecated tool Otter Service
* Added printout of total score to autograder output

**v2.2.2:**

* Added `show_all_public` configuration for grading

**v2.2.1:**

* Added metadata for each test case to Otter Assign format
* Added success and failure messages for test cases
* Added Gmail notifications plugin
* Added timestamps to `otter.Notebook.export` filenames

**v2.2.0:**

* Changed grouping of results to be per-question rather than per-test case

**v2.1.8:**

* Fixed bug in total score calculation when the grade override plugin is used

**v2.1.7:**

* Swapped `IPython.core.inputsplitter.IPythonInputSplitter` for `IPython.core.inputtransformer2.TransformerManager` in `otter.execute.execute_notebook`

**v2.1.6:**

* Fixed `try`/`except` statements in tests per [#228](https://github.com/ucbds-infra/otter-grader/issues/228)
* Added error handling in `GoogleSheetsGradeOverride` plugin for when the Google API hits a rate-limit error

**v2.1.5:**

* Added custom `environment.yml` files in autograder per [#103](https://github.com/ucbds-infra/otter-grader/issues/103)
* Set `display.max_rows` to `None` for pandas to print all rows in summary per [#224](https://github.com/ucbds-infra/otter-grader/issues/224)

**v2.1.4:**

* Added `otter.utils.nullcontext` to be compatible with Python<3.7

**v2.1.3:**

* Added the `notebook_export` plugin event
* Fixed plugin bug resulting from running tests in Otter Assign
* Added creation of plugin collection resulting from Otter Generate for running tests in Otter Assign

**v2.1.2:**

* Added `otter.Notebook.export` format support for Otter Grade
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
