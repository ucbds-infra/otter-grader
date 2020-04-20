# Changelog

**v1.0.0:**

* Changed structure of CLI into four main commands: `otter assign`, `otter check`, `otter generate`, and `otter grade`
* Added `otter assign` command, a forked version of [jassign](https://github.com/okpy/jassign) that works with Otter
* Changed filenames inside the package so that names match commands (e.g. `otter/cli.py` is now `otter/grade.py`)
* Added intercell seeding
* Moved all argparse calls into `bin/otter`
* Made several fixes to `otter check`
* Added indentation to results.json dump in Gradescope container
* Added notebook checker to `otter check`
* `otter generate` and `otter grade` now remove tmp directories on failure
* Fixed `otter.ok_parser.CheckCallWrapper` finding and patching instances of `otter.Notebook`
* Changed behavior of hidden test cases to use individual case `"hidden"` key instead of global `"hidden"` key
* Made use of metadata files in `otter grade` optional
* _Deprecated in v1.0.0:_ the global `test["hidden"]` key in writing OK tests for Otter

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
