# Changelog

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
