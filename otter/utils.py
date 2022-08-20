"""Various utilities for Otter-Grader"""

import importlib
import logging
import os
import pathlib
import random
import re
import string
import shutil
import tempfile

from collections.abc import Mapping
from contextlib import contextmanager, redirect_stdout
from functools import lru_cache
from IPython import get_ipython


# TODO: migrate other uses to this constant
NBFORMAT_VERSION = 4
"""the version of the Jupyter notebook format to use"""

NOTEBOOK_METADATA_KEY = "otter"
"""the key used for all Otter metadata added to a notebook"""


@contextmanager
def block_print():
    """
    Context manager that disables printing to stdout
    """
    with open(os.devnull, "w") as f, redirect_stdout(f):
        yield


@contextmanager
def hide_outputs():
    """
    Context manager for hiding outputs from ``display()`` calls. IPython handles matplotlib outputs 
    specially, so those are supressed too.
    """
    ipy = get_ipython()
    if ipy is None:
        # Not running inside ipython!
        yield
        return
    old_formatters = ipy.display_formatter.formatters
    ipy.display_formatter.formatters = {}
    try:
        yield
    finally:
        ipy.display_formatter.formatters = old_formatters


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """
    Used to generate a dynamic variable name for grading functions

    This function generates a random name using the given length and character set.

    Args:
        size (``int``): length of output name
        chars (``str``, optional): set of characters used to create function name

    Returns:
        ``str``: randomized string name for grading function
    """
    return ''.join(random.choice(chars) for _ in range(size))


def get_variable_type(obj):
    """
    Returns the fully-qualified type string of an object ``obj``

    Args:
        obj (object): the object in question

    Returns:
        ``str``: the fully-qualified type string
    """
    return type(obj).__module__ + "." + type(obj).__name__


def get_relpath(src, dst):
    """
    Returns the relative path from ``src`` to ``dst``

    Args:
        src (``pathlib.Path``): the source directory
        dst (``pathlib.Path``): the destination directory

    Returns:
        ``pathlib.Path``: the relative path
    """
    # osrc = src
    ups = 0
    while True:
        try:
            dst.relative_to(src)
            break
        except ValueError:
            src = src.parent
            ups += 1
    return pathlib.Path(("../" * ups) / dst.relative_to(src))


@contextmanager
def chdir(new_dir):
    """
    Create a context with a different working directory, resetting the working directory on exit.

    Args:
        new_dir (path-like): the directory for the context
    """
    curr_dir = os.getcwd()
    os.chdir(new_dir)

    try: 
        yield

    finally: 
        os.chdir(curr_dir)


def get_source(cell):
    """
    Returns the source code of a cell in a way that works for both nbformat and JSON

    Args:
        cell (``nbformat.NotebookNode``): notebook cell

    Returns:
        ``list`` of ``str``: each line of the cell source stripped of ending line breaks
    """
    source = cell.source
    if isinstance(source, str):
        return re.split("\r?\n", source)
    elif isinstance(source, list):
        return [line.strip("\r\n") for line in source]
    raise TypeError(f"Unknown cell source type: {type(source)}")


@contextmanager
def nullcontext():
    """
    Yields an empty context. Added because ``contextlib.nullcontext`` was added in Python 3.7, so
    earlier versions of Python require this patch.
    """
    yield


@contextmanager
def load_default_file(provided_fn, default_fn, default_disabled=False):
    """
    Reads the contents of a file with an optional default path. If ``proivided_fn`` is not specified
    and ``default_fn`` is an existing file path, the contents of ``default_fn`` are read in place
    of ``provided_fn``. The use of ``default_fn`` can be disabled by setting ``default_disabled``
    to ``True``.
    """
    if provided_fn is None and os.path.isfile(default_fn) and not default_disabled:
        provided_fn = default_fn

    if provided_fn is not None:
        if not os.path.isfile(provided_fn):
            raise FileNotFoundError(f"Could not find specified file: {provided_fn}")

        with open(provided_fn) as f:
            yield f.read()

    else:
        yield


def print_full_width(char, mid_text="", whitespace=" ", ret_str=False, **kwargs):
    """
    Prints a character at the full terminal width. If ``mid_text`` is supplied, this text is printed
    in the middle of the terminal, surrounded by ``whitespace``. Additional kwargs passed to 
    ``print``.

    If ``ret_str`` is true, the string is returned; if not, it is printed directly to the console.
    """
    cols, _ = shutil.get_terminal_size()

    if mid_text:
        left = cols - len(mid_text) - 2 * len(whitespace)
        if left <= 0:
            left = 2
        l, r = left // 2, left // 2
        if left % 2 == 1:
            r += 1

        out = char * l + whitespace + mid_text + whitespace + char * r

    else:
        out = char * cols

    if ret_str:
        return out

    print(out, **kwargs)


# TODO: remove when Otter Assign format v0 is removed
def convert_config_description_dict(configs, for_docs=False):
    """
    Recursively converts a documented list of dictionary configurations into a dictionary with the 
    default values loaded.

    Expects a list of the form:

    .. code-block:: python

        [
            {
                "key": "config_name",
                "description": "a description of the config for documentation",
                "default": True,  # the default config value
            },
            {
                "key": "required_config_name",
                "description": "a description of the config for documentation",
                "required": True,  # indicates that this must be user-specified and has no default
            },
            {
                "key": "nested_config_name",
                "description": "a description of the config for documentation",
                "default": None,
                "subkeys": [  # note that a list is used for nested dict configs
                    {
                        "key": "subconfig",
                        "description": "a nested key",
                        "default": None,
                    }
                ],
            },
        ]

    The list above gets converted to a dictionary mapping each ``key`` to each ``default``:

    .. code-block:: python

        {
            "config_name": True,
            "nested_config_name": None,
        }

    If ``for_docs`` is true, then any specified subkeys are set as the mapped value in the dictionary,
    and if the config is required, its default is set to ``None``.

    .. code-block:: python

        {
            "config_name": True,
            "required_config_name": None,
            "nested_config_name": {
                "subconfig": None,
            },
        }

    Any configurations with ``default`` unspecified have their default value set to ``None``. Any
    configurations marked with ``"required": True`` are not included in the output dict (so that
    they raise a ``KeyError`` if unspecified).

    Args:
        configs (``list[dict[str,object]]``): the configurations with the structure defined above

    Returns:
        ``dict[str,object]``: a dictionary mapping keys to default values
    """
    res = {}
    for d in configs:
        default = d.get("default")
        subkeys = d.get("subkeys")
        if isinstance(default, list) and len(default) > 0 and \
                all(isinstance(e, dict) for e in default):
            default = convert_config_description_dict(default)
        elif for_docs and isinstance(subkeys, list) and len(subkeys) > 0 and \
                all(isinstance(e, dict) for e in subkeys):
            default = convert_config_description_dict(subkeys)
        if not d.get("required", False) or for_docs:
            res[d["key"]] = default
    return res


def assert_path_exists(path_tuples):
    """
    Ensure that a series of file paths exist and are of a specific type, or raise a ``ValueError``.

    Elements of ``path_tuples`` should be 2-tuples where the first element is a string representing 
    the file path and the second element is ``True`` if the path should be a directory, ``False`` if 
    it should be a file, and ``None`` if it doesn't matter.

    Args:
        path_tuples (``list[tuple[str, bool]]``): the list of paths as described above

    Raises:
        ``FileNotFoundError``: if the path does not exist or it is not of the correct type
    """
    for path, is_dir in path_tuples:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} does not exist")
        if is_dir and not os.path.isdir(path):
            raise FileNotFoundError(f"Path {path} is not a directory")
        if is_dir is False and not os.path.isfile(path):
            raise FileNotFoundError(f"Path {path} is not a file")


def knit_rmd_file(rmd_path, pdf_path):
    """
    Use ``rpy2`` and ``rmarkdown::render`` to knit an RMarkdown file to a PDF, allowing errors.

    Args:
        rmd_path (``str``): the path to the Rmd file
        pdf_path (``str``): the path at which to write the PDF
    """
    from rpy2.robjects.packages import importr

    with tempfile.NamedTemporaryFile(mode="w", suffix=".Rmd") as ntf:
        with open(rmd_path) as f:
            contents = f.read()

        contents = "```{r cache = F, include = F}\nknitr::opts_chunk$set(error = TRUE)\n```\n" + \
            contents
        ntf.write(contents)
        ntf.seek(0)

        pdf_path = os.path.abspath(pdf_path)
        rmarkdown = importr("rmarkdown")
        rmarkdown.render(ntf.name, "pdf_document", pdf_path)


class loggers:

    _format = "[%(levelname)s %(name)s.%(funcName)s] %(message)s"
    _instances = {}
    _log_level = logging.WARNING

    @staticmethod
    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("This class is not meant to be instantiated")

    @classmethod
    def get_logger(cls, name):
        """
        Retrieve ``logging.Logger`` with name ``name`` and return it, setting the log level to the 
        class log level.
        """
        if name in cls._instances:
            return cls._instances[name]
        logger = logging.getLogger(name)
        logger.propagate = False  # prevent child loggers from inheriting the handler
        logger.setLevel(cls._log_level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(cls._format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        cls._instances[name] = logger
        return logger

    @classmethod
    def get_level(cls):
        """
        Return the current log level of these loggers.
        """
        return cls._log_level

    @classmethod
    def set_level(cls, log_level):
        """
        Set the log levels for all ``Logger``s created by this class (existing and future).
        """
        cls._log_level = log_level
        for logger in cls._instances.values():
            logger.setLevel(log_level)

    @classmethod
    @contextmanager
    def level_context(cls, log_level):
        """
        Set the log level to a new value temporarily in a context.
        """
        curr_level = cls.get_level()
        cls.set_level(log_level)
        yield
        cls.set_level(curr_level)

    @classmethod
    def reset_level(cls):
        """
        Set the log levels for all ``Loggers`` created by this class (existing and future) back to
        ``logging.WARNING``.
        """
        cls.set_level(logging.WARNING)


class Loggable:
    """
    A class for inheriting from that provides a logger via a class- and instance-accessible field.
    """

    _logger_instance = None

    @classmethod
    def _load_logger(cls):
        """
        Set-up the ``_logger`` field.
        """
        if cls._logger_instance is None:
            name = cls.__module__ + "." + cls.__name__
            cls._logger_instance = loggers.get_logger(name)

    @property
    def _logger(self):
        """
        ``logging.Logger``: the logger instance for this class
        """
        return self._get_logger()

    @classmethod
    def _get_logger(cls):
        """
        Load and return the logger for this class.

        Returns:
            ``logging.Logger``: the logger instance for this class
        """
        cls._load_logger()
        return cls._logger_instance


@lru_cache(None)
def import_or_raise(module):
    """
    Import a module or raise an ``ImportError`` if it is unable to be imported. Return values are
    stored in an LRU cache.
    """
    try:
        return importlib.import_module(module)
    except:
        raise ImportError(f"Could not import required module: {module}")
