"""IPython notebook API for Otter Check"""

import datetime as dt
import inspect
import json
import os
import warnings
import zipfile

from contextlib import contextmanager
from glob import glob
from IPython.display import display, HTML
from textwrap import indent

from .logs import LogEntry, EventType, Log
from .utils import grade_zip_file, grading_mode_disabled, incompatible_with, IPythonInterpreter, \
     list_available_tests, logs_event, resolve_test_info, save_notebook

from ..execute import Checker
from ..export import export_notebook
from ..plugins import PluginCollection
from ..test_files import GradingResults
from ..utils import Loggable, loggers


_OTTER_LOG_FILENAME = ".OTTER_LOG"
_SHELVE = False
_ZIP_NAME_FILENAME = "__zip_filename__"


class Notebook(Loggable):
    """
    Notebook class for in-notebook autograding

    Args:
        nb_path(``str``, optional): path to the notebook being run
        tests_dir (``str``, optional): path to tests directory
        colab (``bool``, optional): whether this notebook is being run on Google Colab; if ``None``,
            this information is automatically parsed from IPython on creation
        jupyterlite (``bool``, optional): whether this notebook is being run on JupyterLite; if
            ``None``, this information is automatically parsed from IPython on creation
    """

    _grading_mode = False

    # overrides tests_dir arg in __init__, used for changing tests dir during grading
    _tests_dir_override = None

    @logs_event(EventType.INIT)
    def __init__(
        self,
        nb_path=None,
        tests_dir="./tests",
        tests_url_prefix=None,
        colab=None,
        jupyterlite=None,
    ):
        global _SHELVE

        interpreter = None
        if colab or IPythonInterpreter.COLAB.value.running():
            interpreter = IPythonInterpreter.COLAB
        elif jupyterlite or IPythonInterpreter.PYOLITE.value.running():
            interpreter = IPythonInterpreter.PYOLITE

        self._interpreter = interpreter

        if self._interpreter is IPythonInterpreter.COLAB and not os.path.isdir(tests_dir):
            raise ValueError(f"Tests directory {tests_dir} does not exist")

        if type(self)._tests_dir_override is not None:
            self._path = type(self)._tests_dir_override
        else:
            self._path = tests_dir

        self._notebook = nb_path
        self._tests_url_prefix = tests_url_prefix
        self._addl_files = []
        self._plugin_collections = {}

        # assume using otter service if there is a .otter file
        otter_configs = glob("*.otter")
        if otter_configs:
            # check that there is only 1 config
            assert len(otter_configs) == 1, "More than 1 otter config file found"

            # load in config file
            with open(otter_configs[0], encoding="utf-8") as f:
                self._config = json.load(f)

            _SHELVE = self._config.get("save_environment", False)
            self._ignore_modules = self._config.get("ignore_modules", [])
            self._vars_to_store = self._config.get("variables", None)

            self._notebook = self._config["notebook"]

    @classmethod
    @contextmanager
    def grading_mode(cls, tests_dir):
        """
        A context manager for the ``Notebook`` grading mode. Yields a pointer to the list of results
        that will be populated during grading.

        **It is the caller's responsibility to maintain the pointer.** The pointer in the ``Checker``
        class will be overwritten when the context exits.
        """
        logger = cls._get_logger()
        logger.info("Entering Notebook grading mode")
        logger.debug(f"Overriding tests directory: {tests_dir}")
        cls._grading_mode = True
        cls._tests_dir_override = tests_dir
        Checker.clear_results()
        Checker.enable_tracking()

        yield Checker.get_results()

        logger.info("Exiting Notebook grading mode")
        cls._grading_mode = False
        cls._tests_dir_override = None
        Checker.disable_tracking()
        Checker.clear_results()

    @incompatible_with(IPythonInterpreter.PYOLITE, throw_error=False)
    def _log_event(self, event_type, results=[], question=None, success=True, error=None, shelve_env={}):
        """
        Logs an event

        Args:
            event_type (``otter.logs.EventType``): the type of event
            results (``list[otter.test_files.abstract_test.TestFile]``, optional):
                the results of any checks recorded by the entry
            question (``str``, optional): the question name for this check
            success (``bool``, optional): whether the operation was successful
            error (``Exception``, optional): the exception thrown by the operation, if applicable
        """
        entry = LogEntry(
            event_type,
            results=results,
            question=question,
            success=success,
            error=error
        )

        if _SHELVE and event_type == EventType.CHECK:
            entry.shelve(
                shelve_env,
                delete=True,
                filename=_OTTER_LOG_FILENAME,
                ignore_modules=self._ignore_modules,
                variables=self._vars_to_store
            )

        entry.flush_to_file(_OTTER_LOG_FILENAME)

    def _resolve_nb_path(self, nb_path, fail_silently=False):
        """
        Attempts to resolve the path to the notebook being run. If ``nb_path`` is ``None``, ``self._notebook``
        is checked, then the working directory is searched for ``.ipynb`` files.

        Args:
            nb_path (``Optional[str]``): path to the notebook
            fail_silently (``bool``): if true, the method does not fail the notebook path can't be
                resolved

        Returns:
            ``str``: resolved notebook path

        Raises:
            ``ValueError``: if no notebooks or too many notebooks are found.
        """
        if nb_path is None and self._notebook is not None:
            nb_path = self._notebook
            if not os.path.isfile(nb_path):
                raise ValueError(f"Expected a notebook file named '{nb_path}' but no such file found")

        elif nb_path is None and glob("*.ipynb"):
            notebooks = glob("*.ipynb")
            if len(notebooks) == 1:
                nb_path = notebooks[0]

        if nb_path is None and not fail_silently:
            raise ValueError("Could not resolve notebook path")

        return nb_path

    @logs_event(EventType.CHECK)
    def check(self, question, global_env=None):
        """
        Runs tests for a specific question against a global environment. If no global environment
        is provided, the test is run against the calling frame's environment.

        Args:
            question (``str``): name of question being graded
            global_env (``dict``, optional): global environment resulting from execution of a single
                notebook

        Returns:
            ``otter.test_files.abstract_test.TestFile``: the grade for the question
        """
        self._logger.info(f"Running check for question: {question}")
        test_path, test_name = resolve_test_info(
            self._path,
            self._resolve_nb_path(None, fail_silently=True),
            self._tests_url_prefix,
            question,
        )

        self._logger.debug(f"Resolved test path: {test_path}")
        self._logger.debug(f"Resolved test name: {test_name}")

        # raise an error for a metadata test on Colab
        if test_name is not None and self._interpreter is IPythonInterpreter.COLAB:
            raise ValueError(f"Test {question} does not exist")

        # ensure that desired test exists
        if not os.path.isfile(test_path):
            raise FileNotFoundError(f"Test {question} does not exist")

        # pass the correct global environment
        if global_env is None:
            self._logger.debug(f"Collecting calling global environment")
            global_env = inspect.currentframe().f_back.f_back.f_globals

        # run the check
        self._logger.debug(f"Calling checker")
        result = Checker.check(test_path, test_name, global_env)

        return question, result, global_env

    @incompatible_with(IPythonInterpreter.COLAB)
    def run_plugin(self, plugin_name, *args, nb_path=None, **kwargs):
        """
        Runs the plugin ``plugin_name`` with the specified arguments. Use ``nb_path`` if the path
        to the notebook is not configured.

        Args:
            plugin_name (``str``): importable name of an Otter plugin that implements the 
                ``from_notebook`` hook
            *args: arguments to be passed to the plugin
            nb_path (``str``, optional): path to the notebook
            **kwargs: keyword arguments to be passed to the plugin

        """
        self._logger.info(f"Running plugin {plugin_name}")
        self._logger.debug(f"Running plugin {plugin_name} with args {args} and kwargs {kwargs}")
        nb_path = self._resolve_nb_path(nb_path)
        if plugin_name in self._plugin_collections:
            pc = self._plugin_collections[plugin_name]
        else:
            pc = PluginCollection([plugin_name], nb_path, {})
            self._plugin_collections[plugin_name] = pc
        pc.run("from_notebook", *args, **kwargs)

    @grading_mode_disabled
    @incompatible_with(IPythonInterpreter.COLAB)
    @logs_event(EventType.TO_PDF)
    def to_pdf(self, nb_path=None, filtering=True, pagebreaks=True, display_link=True, force_save=False):
        """
        Exports a notebook to a PDF using Otter Export

        Args:
            nb_path (``str``, optional): path to the notebook we want to export; will attempt to infer
                if not provided
            filtering (``bool``, optional): set true if only exporting a subset of notebook cells to PDF
            pagebreaks (``bool``, optional): if true, pagebreaks are included between questions
            display_link (``bool``, optional): whether or not to display a download link
            force_save (``bool``, optional): whether or not to display JavaScript that force-saves the
                notebook (only works in Jupyter Notebook classic, not JupyterLab)
        """
        nb_path = self._resolve_nb_path(nb_path)
        self._logger.debug(f"Resolved notebook path: {nb_path}")

        if force_save:
            self._logger.debug("Attempting to force-save notebook")
            saved = save_notebook(nb_path)
            if not saved:
                warnings.warn(
                    "Couldn't automatically save the notebook; we recommend using File > Save & "
                    "Checkpoint and then re-running this cell. The zip file returned by this call "
                    "will use the last saved version of this notebook."
                )
            else:
                self._logger.debug("Force-save successful")

        pdf_path = export_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)
        self._logger.debug(f"Wrote PDF to zip file: {pdf_path}")

        if display_link:
            # create and display output HTML
            out_html = f"""
            <p>Your file has been exported. Download it by right-clicking
            <a href="{pdf_path}" target="_blank">here</a> and selecting <strong>Save Link As</strong>.
            """

            display(HTML(out_html))

    @grading_mode_disabled
    @incompatible_with(IPythonInterpreter.COLAB)
    def add_plugin_files(self, plugin_name, *args, nb_path=None, **kwargs):
        """
        Runs the ``notebook_export`` event of the plugin ``plugin_name`` and tracks the file paths
        it returns to be included when calling ``Notebook.export``.

        Args:
            plugin_name (``str``): importable name of an Otter plugin that implements the 
                ``from_notebook`` hook
            *args: arguments to be passed to the plugin
            nb_path (``str``, optional): path to the notebook
            **kwargs: keyword arguments to be passed to the plugin        
        """
        nb_path = self._resolve_nb_path(nb_path)
        if plugin_name in self._plugin_collections:
            pc = self._plugin_collections[plugin_name]
        else:
            pc = PluginCollection([plugin_name], nb_path, {})
            self._plugin_collections[plugin_name] = pc
        addl_files = pc.run("notebook_export", *args, **kwargs)[0]
        if addl_files is None:
            return
        self._addl_files.extend(addl_files)

    @grading_mode_disabled
    @incompatible_with(IPythonInterpreter.COLAB)
    @logs_event(EventType.END_EXPORT)
    def export(self, nb_path=None, export_path=None, pdf=True, filtering=True, pagebreaks=True, files=[], 
            display_link=True, force_save=False, run_tests=False):
        """
        Exports a submission to a zip file. Creates a submission zipfile from a notebook at ``nb_path``,
        optionally including a PDF export of the notebook and any files in ``files``.

        Args:
            nb_path (``str``, optional): path to the notebook we want to export; will attempt to infer
                if not provided
            export_path (``str``, optional): path at which to write zipfile; defaults to notebook's
                name + ``.zip``
            pdf (``bool``, optional): whether a PDF should be included
            filtering (``bool``, optional): whether the PDF should be filtered; ignored if ``pdf`` is
                ``False``
            pagebreaks (``bool``, optional): whether pagebreaks should be included between questions
                in the PDF
            files (``list`` of ``str``, optional): paths to other files to include in the zip file
            display_link (``bool``, optional): whether or not to display a download link
            force_save (``bool``, optional): whether or not to display JavaScript that force-saves the
                notebook (only works in Jupyter Notebook classic, not JupyterLab)
        """
        self._log_event(EventType.BEGIN_EXPORT)

        nb_path = self._resolve_nb_path(nb_path)
        self._logger.debug(f"Resolved notebook path: {nb_path}")

        if force_save:
            self._logger.debug("Attempting to force-save notebook")
            saved = save_notebook(nb_path)
            if not saved:
                warnings.warn(
                    "Couldn't automatically save the notebook; we recommend using File > Save & "
                    "Checkpoint and then re-running this cell. The zip file returned by this call "
                    "will use the last saved version of this notebook."
                )
            else:
                self._logger.debug("Force-save successful")

        with open(nb_path, "r", encoding="utf-8") as f:
            if len(f.read().strip()) == 0:
                raise ValueError(f"Notebook '{nb_path}' is empty. Please save and checkpoint your "
                    "notebook and rerun this cell.")

        timestamp = dt.datetime.now().strftime("%Y_%m_%dT%H_%M_%S_%f")
        if export_path is None:
            zip_path = ".".join(nb_path.split(".")[:-1]) + "_" + timestamp + ".zip"
        else:
            zip_path = export_path

        self._logger.debug(f"Determined export zip path: {zip_path}")

        zf = zipfile.ZipFile(zip_path, mode="w")
        zf.write(nb_path)

        if pdf:
            pdf_path = export_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)
            if os.path.isfile(pdf_path):
                zf.write(pdf_path)
                self._logger.debug(f"Wrote PDF to zip file: {pdf_path}")
            else:
                warnings.warn("Could not locate a PDF to include")

        if os.path.isfile(_OTTER_LOG_FILENAME):
            zf.write(_OTTER_LOG_FILENAME)
            self._logger.debug("Added Otter log to zip file")

        zip_basename = os.path.basename(zip_path)
        zf.writestr(_ZIP_NAME_FILENAME, zip_basename)
        self._logger.debug(f"Added {_ZIP_NAME_FILENAME} to zip file: '{zip_basename}'")

        dot_otter = glob("*.otter")
        if dot_otter:
            if len(dot_otter) != 1:
                raise ValueError("Too many .otter files (max 1 allowed)")
            dot_otter = dot_otter[0]
            zf.write(dot_otter)
            self._logger.debug(f"Added .otter file to zip file: {dot_otter}")

        for file in files:
            zf.write(file)
            self._logger.debug(f"Added file to zip file: {file}")

        for file in self._addl_files:
            zf.write(file)
            self._logger.debug(f"Added plugin file to zip file: {file}")

        zf.close()

        if run_tests:
            print("Running your submission against local test cases...\n")
            results = grade_zip_file(zip_path, nb_path, self._path)
            print(
                "Your submission received the following results when run against " + \
                "available test cases:\n\n" + indent(results.summary(), "    "))

        if display_link:
            # create and display output HTML
            out_html = """
            <p>Your submission has been exported. Click <a href="{}" download="{}" target="_blank">here</a>
            to download the zip file.</p>
            """.format(zip_path, zip_path)

            display(HTML(out_html))

    @grading_mode_disabled
    @logs_event(EventType.END_CHECK_ALL)
    def check_all(self):
        """
        Runs all tests on this notebook. Tests are run against the current global environment, so any
        tests with variable name collisions will fail.
        """
        self._log_event(EventType.BEGIN_CHECK_ALL)

        tests = list_available_tests(self._path, self._resolve_nb_path(None, fail_silently=True))

        global_env = inspect.currentframe().f_back.f_back.f_back.f_globals

        self._logger.debug(f"Found available tests: {', '.join(tests)}")

        results = []
        if not _SHELVE:
            for test_name in tests:
                results.append(self.check(test_name, global_env))

        else:
            log = Log.from_file(_OTTER_LOG_FILENAME, ascending=False)
            for file in sorted(tests):
                if "__init__.py" not in file:
                    test_name = os.path.splitext(os.path.split(file)[1])[0]

                    entry = log.get_question_entry(test_name)
                    env = entry.unshelve()
                    global_env.update(env)
                    del locals()["env"]

                    result = self.check(test_name, global_env)
                    results.append((test_name, result))

        return GradingResults(results)
