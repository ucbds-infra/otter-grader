"""
IPython notebook API for Otter Check
"""

import inspect
import requests
import json
import os
import re
import zipfile
import pickle
import time
import warnings
import datetime as dt

from getpass import getpass
from glob import glob
from urllib.parse import urljoin
from IPython import get_ipython
from IPython.display import display, HTML, Javascript

from .logs import LogEntry, EventType, Log
from .utils import save_notebook
from ..execute import check
from ..export import export_notebook
from ..plugins import PluginCollection
# from .utils import wait_for_save

_API_KEY = None
_OTTER_STATE_FILENAME = ".OTTER_STATE"
_OTTER_LOG_FILENAME = ".OTTER_LOG"
_SHELVE = False

class TestsDisplay:
    """
    Class for stitching together TestCollectionResults objects and displaying them in HTML and plaintext

    Args:
        results (``list`` of ``tuple(str, TestCollectionResults)``): the test names and results for each test
            to be displayed
    """
    def __init__(self, results):
        self.test_names = [r[0] for r in results]
        self.results = [r[1] for r in results]

    def __repr__(self):
        ret = ""
        for name, result in zip(self.test_names, self.results):
            ret += f"{repr(result)}\n\n"
        return ret

    def _repr_html_(self):
        ret = ""
        for name, result in zip(self.test_names, self.results):
            ret += f"{result._repr_html_()}\n\n"
        return ret



class Notebook:
    """
    Notebook class for in-notebook autograding

    Args:
        nb_path(``str``, optional): path to the notebook being run
        test_dir (``str``, optional): path to tests directory
    """

    # overrides test_dir arg in __init__, used for changing tests dir during grading
    _tests_dir_override = None

    def __init__(self, nb_path=None, test_dir="./tests"):
        try:
            global _API_KEY, _SHELVE
            # assert os.path.isdir(test_dir), "{} is not a directory".format(test_dir)

            if type(self)._tests_dir_override is not None:
                self._path = type(self)._tests_dir_override
            else:
                self._path = test_dir
            self._service_enabled = False
            self._notebook = nb_path

            # assume using otter service if there is a .otter file
            otter_configs = glob("*.otter")
            if otter_configs:
                # check that there is only 1 config
                assert len(otter_configs) == 1, "More than 1 otter config file found"

                # load in config file
                with open(otter_configs[0]) as f:
                    self._config = json.load(f)

                _SHELVE = self._config.get("save_environment", False)
                self._service_enabled = "endpoint" in self._config
                self._ignore_modules = self._config.get("ignore_modules", [])
                self._vars_to_store = self._config.get("variables", None)

                self._notebook = self._config["notebook"]

                if self._service_enabled:
                    # check that config file has required info
                    assert all([key in self._config for key in ["endpoint", "assignment_id", "class_id"]]), "Otter config file missing required information"

                    if "auth" not in self._config:
                        self._config["auth"] = "google"

                    self._google_auth_url = urljoin(self._config["endpoint"], "auth/google")
                    self._default_auth_url = urljoin(self._config["endpoint"], "auth")
                    self._submit_url = urljoin(self._config["endpoint"], "submit")

                    self._auth()

        except Exception as e:
            self._log_event(EventType.INIT, success=False, error=e)
            raise e
        else:
            self._log_event(EventType.INIT)

    # TODO: cut out personal auth?
    def _auth(self):
        """
        Asks student to authenticate with an Otter Service instance if Otter Service is configured
        for this notebook

        Raises:
            ``AssertionError``: if Otter Service is not enabled or an invalid auth provider is indicated
        """
        try:
            global _API_KEY
            assert self._service_enabled, 'notebook not configured for otter service'
            assert self._config["auth"] in ["google", "default"], "invalid auth provider"

            if _API_KEY is not None:
                self._api_key = _API_KEY
                return

            # have users authenticate with OAuth
            if self._config["auth"] == "google":

                    # send them to google login page
                    display(HTML(f"""
                    <p>Please <a href="{self._google_auth_url}" target="_blank">log in</a> to Otter Service
                    and enter your API key below.</p>
                    """))

                    self._api_key = input()
            # else have them auth with default auth
            else:
                print("Please enter a username and password.")
                username = input("Username: ")
                password = getpass("Password: ")

                # in-notebook auth
                response = requests.get(url=self._default_auth_url, params={"username":username, "password":password})
                self._api_key = response.content.decode("utf-8")
                # print("Your API Key is {}\n".format())
                # print("Paste this in and hit enter")
                # self._api_key = input()

            # store API key so we don't re-auth every time
            _API_KEY = self._api_key

        except Exception as e:
            self._log_event(EventType.AUTH, success=False, error=e)
            raise e
        else:
            self._log_event(EventType.AUTH)

    def _log_event(self, event_type, results=[], question=None, success=True, error=None, shelve_env={}):
        """
        Logs an event

        Args:
            event_type (``otter.logs.EventType``): the type of event
            results (``list`` of ``otter.test_files.abstract_test.TestCollectionResults``, optional):
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

    def _resolve_nb_path(self, nb_path):
        """
        Attempts to resolve the path to the notebook being run. If ``nb_path`` is ``None``, ``self._notebook``
        is checked, then the working directory is searched for `.ipynb` files. If none are found, or 
        more than one is found, a ``ValueError`` is raised.

        Args:
            nb_path (``Optional[str]``): path to the notebook
        
        Returns:
            ``str``: resolved notebook path
        
        Raises:
            ``ValueError``: if no notebooks or too many notebooks are found.
        """
        if nb_path is None and self._notebook is not None:
            nb_path = self._notebook

        elif nb_path is None and glob("*.ipynb"):
            notebooks = glob("*.ipynb")
            assert len(notebooks) == 1, "nb_path not specified and > 1 notebook in working directory"
            nb_path = notebooks[0]

        elif nb_path is None:
            raise ValueError("nb_path is None and no otter-service config is available")

        return nb_path

    def check(self, question, global_env=None):
        """
        Runs tests for a specific question against a global environment. If no global environment
        is provided, the test is run against the calling frame's environment.

        Args:
            question (``str``): name of question being graded
            global_env (``dict``, optional): global environment resulting from execution of a single
                notebook

        Returns:
            ``otter.test_files.abstract_test.TestCollectionResults``: the grade for the question
        """
        try:
            test_path = os.path.join(self._path, question + ".py")

            # ensure that desired test exists
            assert os.path.isfile(test_path), "Test {} does not exist".format(question)

            # pass the correct global environment
            if global_env is None:
                global_env = inspect.currentframe().f_back.f_globals

            # run the check
            result = check(test_path, global_env)

        except Exception as e:
            self._log_event(EventType.CHECK, question=question, success=False, error=e, shelve_env=global_env)
            raise e
        else:
            self._log_event(EventType.CHECK, [result], question=question, shelve_env=global_env)

        return result

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
        nb_path = self._resolve_nb_path(nb_path)
        pc = PluginCollection([plugin_name], nb_path, {})
        pc.run("from_notebook", *args, **kwargs)

    # @staticmethod
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
        # self._save_notebook()
        try:
            nb_path = self._resolve_nb_path(nb_path)

            if force_save:
                saved = save_notebook(nb_path)
                if not saved:
                    warnings.warn(
                        "Could not force-save notebook; the results of this call will be based on the last "
                        "saved version of this notebook."
                    )

            # convert(nb_path, filtering=filtering, filter_type=filter_type)
            export_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)

            if display_link:
                # create and display output HTML
                out_html = """
                <p>Your file has been exported. Download it by right-clicking
                <a href="{}" target="_blank">here</a> and selecting <strong>Save Link As</strong>.
                """.format(nb_path[:-5] + "pdf")

                display(HTML(out_html))

        except Exception as e:
            self._log_event(EventType.TO_PDF, success=False, error=e)
            raise e
        else:
            self._log_event(EventType.TO_PDF)

    def export(self, nb_path=None, export_path=None, pdf=True, filtering=True, pagebreaks=True, files=[], 
            display_link=True, force_save=False):
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
        # self._save_notebook()

        try:
            nb_path = self._resolve_nb_path(nb_path)

            if force_save:
                saved = save_notebook(nb_path)
                if not saved:
                    warnings.warn(
                        "Could not force-save notebook; the results of this call will be based on the last "
                        "saved version of this notebook."
                    )

            try:
                with open(nb_path) as f:
                    assert len(f.read().strip()) > 0, \
                        f"Notebook {nb_path} is empty. Please save and checkpoint your notebook and rerun this cell."

            except UnicodeDecodeError:
                with open(nb_path, "r", encoding="utf-8") as f:
                    assert len(f.read().strip()) > 0, \
                        f"Notebook {nb_path} is empty. Please save and checkpoint your notebook and rerun this cell."

            if export_path is None:
                zip_path = ".".join(nb_path.split(".")[:-1]) + ".zip"
            else:
                zip_path = export_path

            zf = zipfile.ZipFile(zip_path, mode="w")
            zf.write(nb_path)

            if pdf:
                pdf_path = ".".join(nb_path.split(".")[:-1]) + ".pdf"
                # convert(nb_path, filtering=filtering, filter_type=filter_type)
                export_notebook(nb_path, filtering=filtering, pagebreaks=pagebreaks)
                zf.write(pdf_path)

            if os.path.isfile(_OTTER_LOG_FILENAME):
                zf.write(_OTTER_LOG_FILENAME)

            if glob("*.otter"):
                assert len(glob("*.otter")) == 1, "Too many .otter files (max 1 allowed)"
                zf.write(glob("*.otter")[0])

            for file in files:
                zf.write(file)

            zf.close()

            if display_link:
                # create and display output HTML
                out_html = """
                <p>Your submission has been exported. Click <a href="{}" target="_blank">here</a>
                to download the zip file.</p>
                """.format(zip_path)

                display(HTML(out_html))

        except Exception as e:
            self._log_event(EventType.END_EXPORT, success=False, error=e)
            raise e
        else:
            self._log_event(EventType.END_EXPORT)

    def check_all(self):
        """
        Runs all tests on this notebook. Tests are run against the current global environment, so any
        tests with variable name collisions will fail.
        """
        # TODO: this should use functions in execute.py to run tests in-sequence so that variable
        # name collisions are accounted for
        self._log_event(EventType.BEGIN_CHECK_ALL)

        try:
            tests = glob(os.path.join(self._path, "*.py"))
            global_env = inspect.currentframe().f_back.f_globals
            results = []
            if not _SHELVE:
                for file in sorted(tests):
                    if "__init__.py" not in file:
                        test_name = os.path.split(file)[1][:-3]
                        result = self.check(test_name, global_env)
                        results.append((test_name, result))
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

        except Exception as e:
            self._log_event(EventType.END_CHECK_ALL, success=False, error=e)
            raise e
        else:
            self._log_event(EventType.END_CHECK_ALL)

        return TestsDisplay(results)

    def submit(self):
        """
        Submits this notebook to an Otter Service instance if Otter Service is configured

        Raises:
            ``AssertionError``: if this notebook is not configured for Otter Service
        """
        assert self._service_enabled, 'notebook not configured for otter service'

        try:
            if not hasattr(self, '_api_key'):
                self._auth()


            notebook_path = os.path.join(os.getcwd(), self._notebook)

            assert os.path.exists(notebook_path) and os.path.isfile(notebook_path), \
            "Could not find notebook: {}".format(self._notebook)

            with open(notebook_path) as f:
                notebook_data = json.load(f)

            notebook_data["metadata"]["assignment_id"] = self._config["assignment_id"]
            notebook_data["metadata"]["class_id"] = self._config["class_id"]

            print("Submitting notebook to server...")

            response = requests.post(self._submit_url, json.dumps({
                "api_key": self._api_key,
                "nb": notebook_data,
            }))

        except Exception as e:
            self._log_event(EventType.SUBMIT, success=False, error=e)
            raise e
        else:
            self._log_event(EventType.SUBMIT)
