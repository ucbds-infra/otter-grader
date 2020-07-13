###############################################
##### In-Notebook Checks for Otter-Grader #####
###############################################

import inspect
import requests
import json
import os
import re
import zipfile
import pickle
import time
import datetime as dt

from getpass import getpass
from glob import glob
from IPython import get_ipython
from IPython.display import display, HTML, Javascript

from .execute import check
from .export import export_notebook
from .logs import LogEntry, EventType, Log
from .utils import wait_for_save

_API_KEY = None
_OTTER_STATE_FILENAME = ".OTTER_STATE"
_OTTER_LOG_FILENAME = ".OTTER_LOG"
_SHELVE = False

class OKTestsDisplay:
    """
    Class for stitching together OKTestsResult objects and displaying them in HTML and plaintext

    Args:
        results (``list`` of ``tuple(str, OKTestsResult)``): the test names and results for each test
            to be displayed
    """
    def __init__(self, results):
        self.test_names = [r[0] for r in results]
        self.results = [r[1] for r in results]
    
    def __repr__(self):
        ret = ""
        for name, result in zip(self.test_names, self.results):
            ret += f"{name}:\n{repr(result)}\n\n"
        return ret

    def _repr_html_(self):
        ret = ""
        for name, result in zip(self.test_names, self.results):
            ret += f"<p><strong>{name}:</strong></p>\n{result._repr_html_()}\n\n"
        return ret

class Notebook:
    """Notebook class for in-notebook autograding
    
    Args:
        test_dir (``str``, optional): path to tests directory
    """

    def __init__(self, test_dir="./tests"):
        try:
            global _API_KEY, _SHELVE
            # assert os.path.isdir(test_dir), "{} is not a directory".format(test_dir)
            
            self._path = test_dir
            self._service_enabled = False
            self._notebook = None
            
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

                # if "notebook" not in self._config:
                #     assert len(glob("*.ipynb")) == 1, "Notebook not specified in otter config file"
                #     self._notebook = glob("*.ipynb")[0]
                    
                # else:
                self._notebook = self._config["notebook"]

                if self._service_enabled:
                    # check that config file has required info
                    assert all([key in self._config for key in ["endpoint", "assignment_id", "class_id"]]), "Otter config file missing required information"

                    if "auth" not in self._config:
                        self._config["auth"] = "google"

                    self._google_auth_url = os.path.join(self._config["endpoint"], "auth/google")
                    self._default_auth_url = os.path.join(self._config["endpoint"], "auth")
                    self._submit_url = os.path.join(self._config["endpoint"], "submit")

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
        """Logs an event

        Args:
            event_type (``otter.logs.EventType``): the type of event
            results (``list`` of ``otter.ok_parser.OKTestsResult``, optional): the results of any checks
                recorded by the entry
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

    # def _save_notebook(self):
    #     """
    #     Runs Jupyter JS to force-save a notebook for use before beginning an export
    #     """
    #     if self._notebook is None:
    #         assert len(glob("*.ipynb")) == 1, "Too many notebooks to infer notebook name"
    #         nb = glob("*.ipynb")[0]
    #     else:
    #         nb = self._notebook
        
    #     if get_ipython() is not None:
    #         display(Javascript("""
    #             require(["base/js/namespace"], function() {
    #                 if ($("span.autosave_status").text().includes("unsaved")) {
    #                     Jupyter.notebook.kernel.execute("_UNSAVED_CHANGES = True");
    #                 } else {
    #                     Jupyter.notebook.kernel.execute("_UNSAVED_CHANGES = False");
    #                 }
    #             });
    #         """))
    #         saved = wait_for_save(nb)
    #         if not saved:
    #             print(
    #                 f"File {nb} was not saved before timeout. Please save and checkpoint "
    #                 "this notebook and rerun this cell."
    #             )

    # def _restart_kernel(self):
    #     """
    #     Runs Jupyter JS to force-save a notebook for use before beginning an export
    #     """
    #     if get_ipython() is not None:
    #         display(Javascript("""
    #             require(["base/js/namespace"], function() {
    #                 Jupyter.notebook.kernel.restart();
    #             });
    #         """))
    #         time.sleep(0.75)

    def check(self, question, global_env=None):
        """
        Runs tests for a specific question against a global environment. If no global environment 
        is provided, the test is run against the calling frame's environment.
        
        Args:
            question (``str``): name of question being graded
            global_env (``dict``, optional): global environment resulting from execution of a single 
                notebook 

        Returns:
            ``otter.ok_parser.OKTestsResult``: the grade for the question
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


    # @staticmethod
    def to_pdf(self, nb_path=None, filtering=True, pagebreaks=True, display_link=True):
        """Exports a notebook to a PDF

        ``filter_type`` can be ``"html"`` or ``"tags"`` if filtering by HTML comments or cell tags,
        respectively. 
        
        Args:
            nb_path (``str``): Path to iPython notebook we want to export
            filtering (``bool``, optional): Set true if only exporting a subset of nb cells to PDF
            pagebreaks (``bool``, optional): If true, pagebreaks are included between questions
            display_link (``bool``, optional): Whether or not to display a download link
        """
        # self._save_notebook()
        try:
            if nb_path is None and self._notebook is not None:
                nb_path = self._notebook

            elif nb_path is None and glob("*.ipynb"):
                notebooks = glob("*.ipynb")
                assert len(notebooks) == 1, "nb_path not specified and > 1 notebook in working directory"
                nb_path = notebooks[0]

            elif nb_path is None:
                raise ValueError("nb_path is None and no otter-service config is available")

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


    def export(self, nb_path=None, export_path=None, pdf=True, filtering=True, pagebreaks=True, files=[], display_link=True):
        """Exports a submission to a zipfile

        Creates a submission zipfile from a notebook at ``nb_path``, optionally including a PDF export
        of the notebook and any files in ``files``.
        
        Args:
            nb_path (``str``): path to notebook we want to export
            export_path (``str``, optional): path at which to write zipfile
            pdf (``bool``, optional): whether a PDF should be included
            filtering (``bool``, optional): whether the PDF should be filtered; ignored if ``pdf`` is
                ``False``
            pagebreaks (``bool``, optional): whether pagebreaks should be included between questions
            files (``list`` of ``str``, optional): paths to other files to include in the zipfile
            display_link (``bool``, optional): whether or not to display a download link
        """
        self._log_event(EventType.BEGIN_EXPORT)
        # self._save_notebook()

        try:
            if nb_path is None and self._notebook is not None:
                nb_path = self._notebook

            elif nb_path is None and glob("*.ipynb"):
                notebooks = glob("*.ipynb")
                assert len(notebooks) == 1, "nb_path not specified and > 1 notebook in working directory"
                nb_path = notebooks[0]

            elif nb_path is None:
                raise ValueError("nb_path is None and no otter-service config is available")

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
        
        return OKTestsDisplay(results)

    def submit(self):
        """Submits this notebook to an Otter Service instance if Otter Service is configured

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

            print(response.text)
        except Exception as e:
            self._log_event(EventType.SUBMIT, success=False, error=e)
            raise e
        else:
            self._log_event(EventType.SUBMIT)
