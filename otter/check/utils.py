"""Utilities for Otter Check"""

import ipylab
import nbformat as nbf
import os
import sys
import tempfile
import time
import warnings
import wrapt

from dataclasses import dataclass
from enum import Enum
from glob import glob
from IPython.core.getipython import get_ipython
from IPython.display import display, Javascript
from ipywidgets import Button, HTML, Output, VBox
from subprocess import PIPE, run
from typing import Any, Callable, Generic, Optional, TYPE_CHECKING, TypeVar, Union

from ..nbmeta_config import NBMetadataConfig
from ..test_files import GradingResults
from ..utils import format_exception


T = TypeVar("T")


def save_notebook(filename: str, timeout: Union[int, float] = 10) -> bool:
    """
    Force-saves a Jupyter notebook by displaying JavaScript.

    Args:
        filename (``str``): path to notebook file being saved
        timeout (``int | float``): number of seconds to wait for save before timing-out

    Returns
        ``bool``: whether the notebook was saved successfully
    """
    if get_ipython() is not None:
        orig_mod_time = os.path.getmtime(filename)
        start = time.time()

        # For classic notebooks
        display(
            Javascript(
                """
            if (typeof Jupyter !== 'undefined') {
                Jupyter.notebook.save_checkpoint();
            }
        """
            )
        )

        # For JupyterLab
        try:
            app = ipylab.JupyterFrontEnd()
            app.commands.execute("docmanager:save")
        except:
            pass

        while time.time() - start < timeout:
            curr_mod_time = os.path.getmtime(filename)
            if orig_mod_time < curr_mod_time and os.path.getsize(filename) > 0:
                return True

            time.sleep(0.2)

        return False

    return True


def grade_zip_file(zip_path: str, nb_arcname: str, tests_dir: str) -> GradingResults:
    """
    Grade a submission zip file in a separate process and return the resulting
    :py:class:`otter.test_files.GradingResults` object.

    Args:
        zip_path (``str``): the path to the submission zip file
        nb_arcname (``str``): the name of the notebook file in the zip file
        tests_dir (``str``): the path to the tests directory

    Returns:
        ``otter.test_files.GradingResults``: the grading results
    """
    import dill

    results_handle, results_path = tempfile.mkstemp(suffix=".pkl")

    try:
        command = [
            sys.executable,
            "-m",
            "otter.check.validate_export",
            "--zip-path",
            zip_path,
            "--nb-arcname",
            nb_arcname,
            "--tests-dir",
            tests_dir,
            "--results-path",
            results_path,
        ]

        # this environment variable is needed to fix #686
        subprocess_env = {**os.environ, "PYDEVD_DISABLE_FILE_VALIDATION": "1"}

        # run the command
        results = run(command, env=subprocess_env, stdout=PIPE, stderr=PIPE)

        print(results.stdout.decode("utf-8"))

        if results.stderr:
            warnings.warn(results.stderr.decode("utf-8"), RuntimeWarning)

        with open(results_path, "rb") as f:
            results = dill.load(f)

        return results

    finally:
        os.close(results_handle)
        os.remove(results_path)


@dataclass
class _Interpreter:
    """
    A class representing a flavor of IPython interpreter.

    Contains attributes for an importable name substring (used to check which interpreter is
    running) and a display name for error messages and the like.
    """

    check_strs: list[str]
    """list of substrings to check for in the IPython interpreter string"""

    display_name: str
    """a display name for this interpreter"""

    def running(self) -> bool:
        """
        Determine whether this interpreter is currently running by checking the string
        representation of the return value of ``IPython.get_ipython``.

        Returns:
            ``bool``: whether this interpreter is running
        """
        ipython_interp = str(get_ipython())
        return any(c in ipython_interp for c in self.check_strs)


class IPythonInterpreter(Enum):
    """
    An enum of different types of IPython interpreters.
    """

    COLAB = _Interpreter(["google.colab"], "Google Colab")
    """the Google Colab interpreter"""

    PYOLITE = _Interpreter(["pyolite.", "pyodide_kernel."], "Jupyterlite")
    """the JupyterLite interpreter"""


def incompatible_with(
    interpreter: IPythonInterpreter, throw_error: bool = True
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    Create a decorator indicating that a method is incompatible with a specific interpreter.
    """

    @wrapt.decorator
    def incompatible(
        wrapped: Callable[..., T], self: "Notebook", args: tuple[Any], kwargs: dict[str, Any]
    ) -> Optional[T]:
        """
        A decorator that raises an error or performs no action (depending on ``throw_error``) if the
        wrapped function is called in an environment running on the specified interpreter.
        """
        if self.interpreter is interpreter:
            if throw_error:
                raise RuntimeError(
                    f"This method is not compatible with {interpreter.value.display_name}"
                )
            else:
                return
        return wrapped(*args, **kwargs)

    return incompatible


@wrapt.decorator
def grading_mode_disabled(
    wrapped: Callable[..., T],
    self: "Notebook",
    args: tuple[Any],
    kwargs: dict[str, Any],
) -> Optional[T]:
    """
    A decorator that returns without calling the wrapped function if the ``Notebook`` grading mode
    is enabled.
    """
    if type(self)._grading_mode:
        return
    return wrapped(*args, **kwargs)


@dataclass
class LoggedEventReturnValue(Generic[T]):
    return_value: T
    question: Optional[str] = None
    shelve_env: Optional[dict[str, Any]] = None


def logs_event(
    event_type: "EventType",
) -> Callable[[Callable[..., LoggedEventReturnValue[T]]], Callable[..., T]]:
    """
    A decorator that ensures each call is logged in the Otter log with type ``event_type``.

    All methods decorated with this function's return value should return either ``None`` or an
    instance of the :py:class:`LoggedEventReturnValue`` dataclass.
    """

    @wrapt.decorator
    def event_logger(
        wrapped: Callable[..., Optional[LoggedEventReturnValue[T]]],
        self: "Notebook",
        args: tuple[Any],
        kwargs: dict[str, Any],
    ) -> T:
        """
        Runs a method, catching any errors and logging the call. Returns the unwrapped return value
        of the wrapped function.
        """
        try:
            ret: Optional[LoggedEventReturnValue[T]] = wrapped(*args, **kwargs)

        except Exception as e:
            self._log_event(event_type, success=False, error=e)
            raise e

        if ret is None:
            ret = LoggedEventReturnValue(None)
        if not isinstance(ret, LoggedEventReturnValue):
            raise TypeError(
                f"Method decorated by logs_event returned value of invalid type: {type(ret)}"
            )

        else:
            self._log_event(
                event_type,
                results=ret.return_value,
                question=ret.question,
                shelve_env=ret.shelve_env,
            )

        return ret.return_value

    return event_logger


def list_test_files(tests_dir: str) -> list[str]:
    """
    Find all of the test files in the specified directory (that is, all ``.py`` files that are not
    named ``__init__.py``) and return their paths in a sorted list.

    Args:
        tests_dir (``str``): the path to the tests directory

    Returns:
        ``list[str]``: the sorted list of all test file paths in ``tests_dir``
    """
    return sorted([file for file in glob(os.path.join(tests_dir, "*.py")) if file != "__init__.py"])


def list_available_tests(tests_dir: str, nbmeta_config: NBMetadataConfig) -> list[str]:
    """
    Get a list of available questions by searching the tests directory (if present) or the notebook
    metadata.

    Args:
        tests_dir (``str``): the path to the tests directory
        nbmeta_config (``otter.nbmeta_config.NBMetadataConfig``): the notebook metadata config

    Returns:
        ``list[str]``: the sorted list of question names
    """
    get_stem = lambda p: os.path.splitext(os.path.basename(p))[0]

    if tests_dir and os.path.isdir(tests_dir):
        tests = map(get_stem, list_test_files(tests_dir))

    else:
        tests = list(nbmeta_config.tests.keys())

    return sorted(tests)


def resolve_test_info(
    tests_dir: str,
    nb_path: Optional[str],
    tests_url_prefix: Optional[str],
    question: str,
) -> tuple[str, Optional[str]]:
    """
    Determine the test path and test name.

    If ``tests_url_prefix`` is specified, the test file is downloaded from the URL
    ``{tests_url_prefix}/{question}.py`` and saved to the file ``{tests_dir}/{question}.py``. If
    ``tests_dir`` does not already exist, it is created.

    Args:
        tests_dir (``str``): the path to the directory of tests
        nb_path (``str | None``): the path to the notebook
        tests_url_prefix (``str | None``): the prefix of a URL to the test file
        question (``str``): the question name

    Returns:
        ``tuple[str, str | None]``: the test path and test name (if applicable)
    """
    if tests_url_prefix is not None:
        if not IPythonInterpreter.PYOLITE.value.running():
            raise ValueError("Downloading test files from URLs is only supported on JupyterLite")

        import pyodide

        test_url = (
            f"{tests_url_prefix}{'/' if not tests_url_prefix.endswith('/') else ''}{question}.py"
        )
        text = pyodide.open_url(test_url).getvalue()

        os.makedirs(tests_dir, exist_ok=True)

        test_path = os.path.join(tests_dir, f"{question}.py")
        test_name = None

        with open(test_path, "w+") as f:
            f.write(text)

    elif tests_dir and os.path.isdir(tests_dir):
        if not os.path.isfile(os.path.join(tests_dir, question + ".py")):
            raise FileNotFoundError(f"Test {question} does not exist")

        test_path = os.path.join(tests_dir, question + ".py")
        test_name = None

    else:
        if nb_path is None:
            raise ValueError("Tests directory does not exist and no notebook path provided")

        test_path = nb_path
        test_name = question

    return test_path, test_name


def display_pdf_confirmation_widget(
    message: Optional[str], pdf_error: Optional[Exception], callback: Callable[..., Any]
) -> None:
    """
    Display a widget to the user to acknowledge that a PDF will not be included in their submission
    zip.

    Args:
        message (``str | None``): a custom message to use
        callback (``callable``): a callback function to execute after the user ACKs
    """
    o = Output()

    def wrapped_callback(*_: tuple[Any]):
        with o:
            callback()

    if not message:
        message = (
            "Your notebook could not be exported as a PDF. To continue exporting your "
            "submission, please click the button below."
        )

    message_html = f"""<p style="margin: 0">{message}</p>"""
    if pdf_error is not None:
        message_html += f"""<pre>{format_exception(pdf_error)}</pre>"""

    t = HTML(message_html)
    b = Button(description="Continue export", button_style="warning")
    b.on_click(wrapped_callback)
    m = HTML("""<div style="height: 10px; width: 100%"></div>""")

    display(VBox([t, b, m, o]))


if TYPE_CHECKING:
    from .logs import EventType
    from .notebook import Notebook
