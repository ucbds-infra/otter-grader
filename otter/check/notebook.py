"""IPython notebook API for Otter Check"""

import datetime as dt
import inspect
import json
import nbformat as nbf
import os
import sys
import warnings
import zipfile

from glob import glob
from IPython.display import display, HTML
from textwrap import indent
from typing import Any, ClassVar, Optional, Union

from .logs import EventType, Log, LogEntry
from .utils import (
    display_pdf_confirmation_widget,
    grade_zip_file,
    grading_mode_disabled,
    incompatible_with,
    IPythonInterpreter,
    list_available_tests,
    LoggedEventReturnValue,
    logs_event,
    resolve_test_info,
    save_notebook,
)
from ..execute import Checker
from ..export import export_notebook
from ..logging import Loggable
from ..nbmeta_config import NBMetadataConfig
from ..plugins import PluginCollection
from ..test_files import GradingResults, TestFile


OTTER_LOG_FILENAME = ".OTTER_LOG"
_ZIP_NAME_FILENAME = "__zip_filename__"


class Notebook(Loggable):
    """
    Notebook class for in-notebook autograding

    Args:
        nb_path (``str | None``): path to the notebook being run
        tests_dir (``str``): path to tests directory
        tests_url_prefix (``str | None``): a URL prefix to use to download test files
    """

    _grading_mode: ClassVar[bool] = False
    """whether Otter is currently in grading mode"""

    _shelve: ClassVar[bool] = False
    """whether to shelve the global environment in log entries"""

    _tests_dir_override: ClassVar[Optional[str]] = None
    """an override for the path to the tests directory"""

    _notebook: Optional[str]
    """the path to the notebook file"""

    _tests_dir: str
    """the path to the tests directory"""

    _tests_url_prefix: Optional[str]
    """a URL prefix to use for downloading test files"""

    _addl_files: list[str]
    """a list of additional file paths to include in the exported submission zip"""

    _plugin_collections: dict[str, PluginCollection]
    """a cache of ``PluginCollection`` objects for each plugin invoked in the notebook"""

    interpreter: Optional[IPythonInterpreter]
    """the interpreter that is currently running (if not the standard IPython interpreter)"""

    _nbmeta_config: NBMetadataConfig
    """the metadata config from the notebook"""

    _config: Optional[dict[str, Any]] = None
    """the config loaded from the .otter file if there was one"""

    _ignore_modules: Optional[list[str]] = None
    """a list of modules to ignore when serializing environments"""

    _vars_to_store: Optional[dict[str, str]] = None
    """a map of var names -> type name to use when serializing environments"""

    @logs_event(EventType.INIT)
    def __init__(
        self,
        nb_path: Optional[str] = None,
        tests_dir: str = "./tests",
        tests_url_prefix: Optional[str] = None,
    ):
        interpreter = None
        for i in IPythonInterpreter:
            if i.value.running():
                interpreter = i
                break

        self.interpreter = interpreter

        if self.interpreter is IPythonInterpreter.COLAB and not os.path.isdir(tests_dir):
            raise ValueError(f"Tests directory {tests_dir} does not exist")

        cls = type(self)
        if cls._tests_dir_override is not None:
            self._tests_dir = cls._tests_dir_override
        else:
            self._tests_dir = tests_dir

        self._notebook = nb_path
        self._notebook = self._resolve_nb_path(nb_path, fail_silently=True)
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

            if not isinstance(self._config, dict):
                raise ValueError(f'"{otter_configs[0]}" does not contain a valid config')

            type(self)._shelve = self._config.get("save_environment", False)
            self._ignore_modules = self._config.get("ignore_modules", [])
            self._vars_to_store = self._config.get("variables", None)

            self._notebook = self._config["notebook"]

        if self._notebook:
            self._nbmeta_config = NBMetadataConfig.from_notebook(
                nbf.read(self._notebook, nbf.NO_CONVERT)
            )
        else:
            self._nbmeta_config = NBMetadataConfig()

    @classmethod
    def init_grading_mode(cls, tests_dir: str):
        logger = cls._get_logger()
        logger.info("Entering Notebook grading mode")
        logger.debug(f"Overriding tests directory: {tests_dir}")
        cls._grading_mode = True
        cls._tests_dir_override = tests_dir
        Checker.clear_results()
        Checker.enable_tracking()

    @incompatible_with(IPythonInterpreter.PYOLITE, throw_error=False)
    def _log_event(
        self,
        event_type: EventType,
        results: Optional[Union[GradingResults, TestFile]] = None,
        question: Optional[str] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        shelve_env: Optional[dict[str, Any]] = None,
    ):
        """
        Log an event to Otter's client log file.

        Args:
            event_type (``otter.logs.EventType``): the type of event
            results (``otter.test_files.TestFile | None``): the results of any checks recorded
                by the entry
            question (``str | None``): the question name for this check
            success (``bool``): whether the operation was successful
            error (``Exception | None``): the exception thrown by the operation, if applicable
            shelve_env (``dict[str, Any] | None``): the environment to shelve
        """
        entry = LogEntry(
            event_type, results=results, question=question, success=success, error=error
        )

        if type(self)._shelve and event_type == EventType.CHECK:
            if not isinstance(shelve_env, dict):
                raise TypeError(f"shelve_env has an invalid type: {type(shelve_env)}")

            entry.shelve(
                shelve_env,
                delete=True,
                filename=OTTER_LOG_FILENAME,
                ignore_modules=self._ignore_modules,
                variables=self._vars_to_store,
            )

        entry.flush_to_file(OTTER_LOG_FILENAME)

    def _resolve_nb_path(
        self, nb_path: Optional[str], fail_silently: bool = False
    ) -> Optional[str]:
        """
        Attempts to resolve the path to the notebook being run. If ``nb_path`` is ``None``,
        ``self._notebook`` is checked, then the working directory is searched for ``.ipynb`` files.

        Args:
            nb_path (``str | None``): path to the notebook
            fail_silently (``bool``): if true, the method does not fail the notebook path can't be
                resolved

        Returns:
            ``str | None``: resolved notebook path or ``None`` if it can't be resolved and
                ``fail_silently`` was true

        Raises:
            ``ValueError``: if no notebooks or too many notebooks are found and ``fail_silently`` is
                false
        """
        # if in grading mode, don't attempt to resolve the notebook path, since the tests path was
        # already overridden in __init__
        if type(self)._grading_mode:
            return nb_path

        if nb_path is None and self._notebook is not None:
            nb_path = self._notebook
            if not os.path.isfile(nb_path):
                raise ValueError(
                    f"Expected a notebook file named '{nb_path}' but no such file found"
                )

        elif nb_path is None and glob("*.ipynb"):
            notebooks = glob("*.ipynb")
            if len(notebooks) == 1:
                nb_path = notebooks[0]

        if nb_path is None and not fail_silently:
            raise ValueError("Could not resolve notebook path")

        return nb_path

    @logs_event(EventType.CHECK)
    def check(
        self, question: str, global_env: Optional[dict[str, Any]] = None
    ) -> LoggedEventReturnValue[TestFile]:
        """
        Runs tests for a specific question against a global environment. If no global environment
        is provided, the test is run against the calling frame's environment.

        Args:
            question (``str``): name of question being graded
            global_env (``dict[str, object]  | None``): a global environment in which to run the
                tests

        Returns:
            ``otter.test_files.abstract_test.TestFile``: the grade for the question
        """
        self._logger.info(f"Running check for question: {question}")
        test_path, test_name = resolve_test_info(
            self._tests_dir,
            self._notebook,
            self._tests_url_prefix,
            question,
        )

        self._logger.debug(f"Resolved test path: {test_path}")
        self._logger.debug(f"Resolved test name: {test_name}")

        # raise an error for a metadata test on Colab
        if test_name is not None and self.interpreter is IPythonInterpreter.COLAB:
            raise ValueError(f"Test {question} does not exist")

        # ensure that desired test exists
        if not os.path.isfile(test_path):
            raise FileNotFoundError(f"Test {question} does not exist")

        # pass the correct global environment
        if global_env is None:
            self._logger.debug(f"Collecting calling global environment")
            frame = inspect.currentframe().f_back.f_back
            # I have NO IDEA why but in python 3.13 ONLY WHEN RUNNING TESTS (?!?!) there is an
            # additional frame for wrapt. I spent h o u r s trying to figure out why but I was
            # unsuccessful.
            if f"{os.path.sep}wrapt{os.path.sep}" in frame.f_code.co_filename:
                frame = frame.f_back
            global_env = frame.f_globals

        # run the check
        self._logger.debug(f"Calling checker")
        result = Checker.check(test_path, self._nbmeta_config, test_name, global_env)

        return LoggedEventReturnValue(result, question=question, shelve_env=global_env)

    @incompatible_with(IPythonInterpreter.COLAB)
    def run_plugin(
        self,
        plugin_name: str,
        *args: Any,
        nb_path: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Runs the plugin ``plugin_name`` with the specified arguments. Use ``nb_path`` if the path
        to the notebook is not configured.

        Args:
            plugin_name (``str``): importable name of an Otter plugin that implements the
                ``from_notebook`` hook
            *args: arguments to be passed to the plugin
            nb_path (``str | None``): path to the notebook
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
    def to_pdf(
        self,
        nb_path: Optional[str] = None,
        filtering: bool = True,
        pagebreaks: bool = True,
        display_link: bool = True,
        force_save: bool = False,
    ):
        """
        Exports a notebook to a PDF using Otter Export

        Args:
            nb_path (``str | None``): path to the notebook we want to export; will attempt to infer
                if not provided
            filtering (``bool``): set true if only exporting a subset of notebook cells to PDF
            pagebreaks (``bool``): if true, pagebreaks are included between questions
            display_link (``bool``): whether or not to display a download link
            force_save (``bool``): whether or not to display JavaScript that force-saves the
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
    def add_plugin_files(
        self,
        plugin_name: str,
        *args: Any,
        nb_path: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Runs the ``notebook_export`` event of the plugin ``plugin_name`` and tracks the file paths
        it returns to be included when calling ``Notebook.export``.

        Args:
            plugin_name (``str``): importable name of an Otter plugin that implements the
                ``from_notebook`` hook
            *args: arguments to be passed to the plugin
            nb_path (``str | None``): path to the notebook
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
    def export(
        self,
        nb_path: Optional[str] = None,
        export_path: Optional[str] = None,
        pdf: bool = True,
        filtering: bool = True,
        pagebreaks: bool = True,
        files: Optional[list[str]] = None,
        display_link: bool = True,
        force_save: bool = False,
        run_tests: bool = False,
        ignore_log: bool = False,
    ):
        """
        Export a submission zip file.

        Creates a submission zipfile from a notebook at ``nb_path``, optionally including a PDF
        export of the notebook and any files in ``files``.

        If ``run_tests`` is true, the zip is validated by running it against local test cases in a
        separate Python process. The results of this run are printed to stdout.

        Args:
            nb_path (``str | None``): path to the notebook we want to export; will attempt to infer
                if not provided
            export_path (``str | None``): path at which to write zipfile; defaults to
                ``{notebook name}_{timestamp}.zip``
            pdf (``bool``): whether a PDF should be included
            filtering (``bool``): whether the PDF should be filtered
            pagebreaks (``bool``): whether pagebreaks should be included between questions in the
                PDF
            files (``list[str] | None``): paths to other files to include in the zip file
            display_link (``bool``): whether or not to display a download link
            force_save (``bool``): whether or not to display JavaScript that force-saves the
                notebook (only works in Jupyter Notebook classic, not JupyterLab)
            run_tests (``bool``): whether to validating the resulting submission zip against local
                test cases
            ignore_log (``bool``): whether to exclude the .OTTER_LOG file from the submission zip
        """
        self._log_event(EventType.BEGIN_EXPORT)

        files = [] if files is None else files

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
                raise ValueError(
                    f"Notebook '{nb_path}' is empty. Please save and checkpoint your "
                    "notebook and rerun this cell."
                )

            f.seek(0)

        timestamp = dt.datetime.now().strftime("%Y_%m_%dT%H_%M_%S_%f")
        if export_path is None:
            zip_path = ".".join(nb_path.split(".")[:-1]) + "_" + timestamp + ".zip"
        else:
            zip_path = export_path

        self._logger.debug(f"Determined export zip path: {zip_path}")

        zf = zipfile.ZipFile(zip_path, mode="w")
        zf.write(nb_path)

        pdf_path, pdf_created, pdf_error = None, True, None
        if pdf:
            try:
                pdf_path = export_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)
            except Exception as e:
                pdf_error = e
            if pdf_path and os.path.isfile(pdf_path):
                pdf_created = True
                zf.write(pdf_path)
                self._logger.debug(f"Wrote PDF to zip file: {pdf_path}")
            else:
                pdf_created = False
                warnings.warn("Could not locate a PDF to include")

        def continue_export():
            if not ignore_log and os.path.isfile(OTTER_LOG_FILENAME):
                zf.write(OTTER_LOG_FILENAME)
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
                if os.path.isdir(file):
                    sub_files = glob(f"{file}/**/*.*", recursive=True)
                    for sub_file in sub_files:
                        zf.write(sub_file)
                else:
                    zf.write(file)
                self._logger.debug(f"Added file to zip file: {file}")

            for file in self._addl_files:
                zf.write(file)
                self._logger.debug(f"Added plugin file to zip file: {file}")

            zf.close()

            if run_tests:
                print("Running your submission against local test cases...\n")
                results = grade_zip_file(zip_path, nb_path, self._tests_dir)
                print(
                    "Your submission received the following results when run against "
                    + "available test cases:\n\n"
                    + indent(results.summary(), "    ")
                )

            if display_link:
                # create and display output HTML
                out_html = f"""
                    <p>
                        Your submission has been exported. Click
                        <a href="{zip_path}" download="{zip_path}" target="_blank">here</a> to download
                        the zip file.
                    </p>
                """

                display(HTML(out_html))

        if pdf_created or not self._nbmeta_config.require_no_pdf_confirmation:
            if pdf_error is not None:
                raise pdf_error
            continue_export()
        else:
            display_pdf_confirmation_widget(
                self._nbmeta_config.export_pdf_failure_message, pdf_error, continue_export
            )

    @grading_mode_disabled
    @logs_event(EventType.END_CHECK_ALL)
    def check_all(self):
        """
        Runs all tests on this notebook. Tests are run against the current global environment, so
        any tests with variable name collisions will fail.
        """
        self._log_event(EventType.BEGIN_CHECK_ALL)

        tests = list_available_tests(self._tests_dir, self._nbmeta_config)

        frame = inspect.currentframe().f_back.f_back
        # I have NO IDEA why but in python 3.13 ONLY WHEN RUNNING TESTS (?!?!) there is an
        # additional frame for wrapt. I spent h o u r s trying to figure out why but I was
        # unsuccessful.
        if f"{os.path.sep}wrapt{os.path.sep}" in frame.f_code.co_filename:
            frame = frame.f_back
        # do it again since there are 2 decorators on this method
        frame = frame.f_back
        if f"{os.path.sep}wrapt{os.path.sep}" in frame.f_code.co_filename:
            frame = frame.f_back

        global_env = frame.f_globals

        self._logger.debug(f"Found available tests: {', '.join(tests)}")

        results = []
        if not type(self)._shelve:
            for test_name in tests:
                results.append(self.check(test_name, global_env))

        else:
            log = Log.from_file(OTTER_LOG_FILENAME, ascending=False)
            for file in sorted(tests):
                if "__init__.py" not in file:
                    test_name = os.path.splitext(os.path.split(file)[1])[0]

                    entry = log.get_question_entry(test_name)
                    env = entry.unshelve()
                    global_env.update(env)
                    del locals()["env"]

                    result = self.check(test_name, global_env)
                    results.append((test_name, result))

        return LoggedEventReturnValue(GradingResults(results))
