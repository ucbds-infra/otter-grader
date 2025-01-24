"""Logging for Otter Check"""

import datetime as dt
import dill
import os
import tempfile
import types

from collections.abc import Iterable, Iterator
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING, Union

from ..utils import QuestionNotInLogException


class EventType(Enum):
    """
    Enum of event types for log entries
    """

    AUTH = 1
    """an auth event"""

    BEGIN_CHECK_ALL = 2
    """beginning of a check-all cell"""

    BEGIN_EXPORT = 3
    """beginning of an assignment export"""

    CHECK = 4
    """a check of a single question"""

    END_CHECK_ALL = 5
    """ending of a check-all cell"""

    END_EXPORT = 6
    """ending of an assignment export"""

    INIT = 7
    """initialization of an :py:class:`otter.check.notebook.Notebook` object"""

    SUBMIT = 8
    """submission of an assignment (unused since Otter Service was removed)"""

    TO_PDF = 9
    """PDF export of a notebook (not used during a submission export)"""


class LogEntry:
    """
    An entry in Otter's log. Tracks event type, grading results, success of operation, and errors
    thrown.

    Args:
        event_type (``EventType``): the type of event for this entry
        results (``otter.test_files.TestFile | otter.test_files.GradingResults | None``): the
            results of grading if this is an ``EventType.CHECK`` or ``EventType.END_CHECK_ALL``
            record
        question (``str``): the question name for an ``EventType.CHECK`` record
        success (``bool``): whether the operation was successful
        error (``Exception``): an error thrown by the process being logged if any
    """

    event_type: EventType
    """the entry type"""

    shelf: Optional[bytes]
    """a pickled environment stored as a bytes string"""

    not_shelved: list[str]
    """a list of variable names that were not added to the shelf"""

    results: Optional[Union["GradingResults", "TestFile"]]
    """grading results if this is an ``EventType.CHECK`` entry"""

    question: Optional[str]
    """question name if this is a check entry"""

    success: bool
    """whether the operation tracked by this entry was successful"""

    error: Optional[Exception]
    """an error thrown by the tracked process if applicable"""

    timestamp: dt.datetime
    """timestamp of event in UTC"""

    def __init__(
        self,
        event_type: EventType,
        shelf: Optional[bytes] = None,
        results: Optional["GradingResults"] = None,
        question: Optional[str] = None,
        success: bool = True,
        error: Optional[Exception] = None,
    ):
        if event_type not in EventType:
            raise TypeError("event_type has is not an EventType")

        self.event_type = event_type
        self.shelf = shelf
        self.not_shelved = []
        self.results = results
        self.question = question
        self.timestamp = dt.datetime.now(dt.timezone.utc)
        self.success = success
        self.error = error

    def __repr__(self):
        if self.question:
            return (
                "otter.logs.LogEntry(event_type={}, question={}, success={}, timestamp={})".format(
                    self.event_type, self.question, self.success, self.timestamp.isoformat()
                )
            )

        return "otter.logs.LogEntry(event_type={}, success={}, timestamp={})".format(
            self.event_type, self.success, self.timestamp.isoformat()
        )

    def get_results(self) -> Optional[Union["GradingResults", "TestFile"]]:
        """
        Get the results stored in this log entry

        Returns:
            ``otter.test_files.GradingResults | otter.test_files.TestFile | None``: the results at
                this entry if this is an ``EventType.CHECK`` record
        """
        assert self.event_type is EventType.CHECK, "this record type has no results"
        if isinstance(self.results, list):
            return self.results[0]
        return self.results

    def raise_error(self):
        """
        Raises the error stored in this entry

        Raises:
            ``Exception``: the error stored at this entry, if present
        """
        if self.error is not None:
            raise self.error

    def flush_to_file(self, filename: str):
        """
        Appends this log entry (pickled) to a file

        Args:
            filename (``str``): the path to the file to append this entry
        """
        try:
            file = open(filename, "ab+")
            dill.dump(self, file)

        except OSError:
            raise Exception(
                "Could not create the log file as the file system is read-only. Please contact your "
                "instructor before continuing on this assignment."
            )

        finally:
            if "file" in locals():
                file.close()

    def shelve(
        self,
        env: dict[str, Any],
        delete: bool = False,
        filename: Optional[str] = None,
        ignore_modules: Optional[list[str]] = None,
        variables: Optional[dict[str, str]] = None,
    ) -> "LogEntry":
        """
        Stores an environment ``env`` in this log entry using dill as a ``bytes`` object in this entry
        as the ``shelf`` attribute. Writes names of any variables in ``env`` that are not stored to
        the ``not_shelved`` attribute.

        If ``delete`` is ``True``, old environments in the log at ``filename`` for this question are
        cleared before writing ``env``. Any module names in ``ignore_modules`` will have their functions
        ignored during pickling.

        Args:
            env (``dict``): the environment to pickle
            delete (``bool``): whether to delete old environments
            filename (``str``): path to log file; ignored if ``delete`` is ``False``
            ignore_modules (``list[str]``): module names to ignore during pickling
            variables (``dict[str, str]``): map of variable name to type string indicating **only**
                variables to include (all variables not in this dictionary will be ignored)

        Returns:
            ``LogEntry``: this entry
        """
        # delete old entry without reading entire log
        if delete:
            assert filename, "old env deletion indicated but no log filename provided"
            try:
                # copy the existing log to a temporary file so that we can edit the original
                with tempfile.TemporaryFile() as tf:
                    with open(filename, "rb") as f:
                        tf.write(f.read())
                    tf.seek(0)
                    os.system(f"rm -f {filename}")
                    while True:
                        try:
                            entry = dill.load(tf)

                            if entry.question == self.question and entry.shelf is not None:

                                # only edit variables if it's not provided
                                if variables is None:
                                    variables = list(entry.unshelve().keys())
                                    variables_stored = None
                                else:
                                    variables_stored = list(entry.unshelve().keys())

                                entry.shelf = None

                            entry.flush_to_file(filename)

                            del locals()["entry"]

                        except EOFError:
                            break

            except FileNotFoundError:
                pass

        try:
            if isinstance(variables_stored, list):
                variables = {k: v for k, v in variables.items() if k in variables_stored}
        except UnboundLocalError:
            pass

        shelf_contents, not_shelved = LogEntry.shelve_environment(
            env, variables=variables, ignore_modules=ignore_modules
        )
        self.shelf = shelf_contents
        self.not_shelved = not_shelved
        return self

    def unshelve(self, global_env: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Parses a ``bytes`` object stored in the ``shelf`` attribute and unpickles the object stored
        there using dill. Updates the ``__globals__`` of any functions in ``shelf`` to include elements
        in the shelf. Optionally includes the env passed in as ``global_env``.

        Args:
            global_env (``dict[str, Any]``): a global env to include in unpickled function globals

        Returns:
            ``dict[str, Any]``: the shelved environment
        """
        if not self.shelf:
            raise ValueError("There is no shelf in this entry")

        if global_env is None:
            global_env = {}

        # read bytes in self.shelf and load with dill
        with tempfile.TemporaryFile() as tf:
            tf.write(self.shelf)
            tf.seek(0)
            shelf = dill.load(tf)

        # add the unpickled env and global_env to all function __globals__
        for v in shelf.values():
            if type(v) == types.FunctionType:
                v.__globals__.update(shelf)
                v.__globals__.update(global_env)

        return shelf

    @staticmethod
    def sort_log(log: list["LogEntry"], ascending: bool = True) -> list["LogEntry"]:
        """
        Sorts a list of log entries by timestamp.

        Args:
            log (``list[LogEntry]``): the log to sort
            ascending (``bool``): whether the log should be sorted in ascending (chronological)
                order

        Returns:
            ``list[LogEntry]``: the sorted log
        """
        if ascending:
            return list(sorted(log, key=lambda l: l.timestamp))
        return list(sorted(log, key=lambda l: l.timestamp, reverse=True))

    @staticmethod
    def log_from_file(filename: str, ascending: bool = True) -> list["LogEntry"]:
        """
        Reads a log file and returns a sorted list of the log entries pickled in that file.

        Args:
            filename (``str``): the path to the log
            ascending (``bool``): whether the log should be sorted in ascending (chronological)
                order

        Returns:
            ``list[LogEntry]``: the sorted log
        """
        try:
            file = open(filename, "rb")

            log = []
            while True:
                try:
                    log.append(dill.load(file))
                except EOFError:
                    break

            log = list(sorted(log, key=lambda l: l.timestamp, reverse=not ascending))

            return log

        finally:
            if "file" in locals():
                file.close()

    @staticmethod
    def shelve_environment(
        env: dict[str, Any],
        variables: Optional[Union[dict[str, str], list[str]]] = None,
        ignore_modules: Optional[list[str]] = None,
    ) -> tuple[bytes, list[str]]:
        """
        Pickles an environment ``env`` using dill, ignoring any functions whose module is listed in
        ``ignore_modules``. Returns the pickle file contents as a ``bytes`` object and a list of
        variable names that were unable to be shelved/ignored during shelving.

        Args:
            env (``dict[str, Any]``): the environment to shelve
            variables (``dict[str, str] | list[str] | None``): a map of variable name to type string
                indicating **only** variables to include (all variables not in this dictionary will
                be ignored) or a list of variable names to include regardless of type
            ignore_modules (``list[str] | None``): the module names to ignore

        Returns:
            ``tuple[bytes, list[str]``: the pickled environment and list of variable names that were
                not shelved
        """
        from .notebook import Notebook

        if ignore_modules is None:
            ignore_modules = []

        not_shelved = []
        filtered_env = {}
        for k, v in env.items():

            # don't store modules or otter.Notebook instances
            if type(v) == types.ModuleType or type(v) == Notebook:
                not_shelved.append(k)

            # ignore any functions whose __module__ is in ignore_modules
            elif type(v) == types.FunctionType and v.__module__ in ignore_modules:
                not_shelved.append(k)

            # ensure object is pickleable by attempting dump and if so add to filtered_env
            else:
                try:
                    dill.dumps(v)

                    # only store variable names in variables that have the correct type
                    if (variables and k in variables) or not variables:
                        full_type = type(v).__module__ + "." + type(v).__name__

                        if (
                            (isinstance(variables, dict) and full_type == variables[k])
                            or isinstance(variables, list)
                            or not variables
                        ):
                            filtered_env[k] = v

                        else:
                            not_shelved.append(k)

                    else:
                        not_shelved.append(k)

                except:
                    not_shelved.append(k)

        # dump filtered_env to a temporary file and then return the bytes and not_shelved list
        with tempfile.TemporaryFile() as tf:
            dill.dump(filtered_env, tf)
            tf.seek(0)
            shelf_contents = tf.read()

        return shelf_contents, not_shelved


class Log(Iterable[LogEntry]):
    """
    A class for reading and interacting with a log. Allows you to iterate over the entries in the log
    and supports integer indexing. *Does not support editing the log file.*

    Args:
        entries (``list[LogEntry]``): the list of entries for this log
        ascending (``bool``): whether the log is sorted in ascending (chronological) order;
            default ``True``
    """

    entries: list[LogEntry]
    """the list of log entries in this log"""

    ascending: bool
    """whether ``entries`` is sorted chronologically; ``False`` indicates reverse-chronological order"""

    def __init__(self, entries: list[LogEntry], ascending: bool = True):
        self.entries = entries
        self.ascending = ascending

    def __repr__(self):
        return "otter.logs.Log([\n  {}\n])".format(",\n  ".join([repr(e) for e in self.entries]))

    def __getitem__(self, idx: int) -> LogEntry:
        return self.entries[idx]

    def __iter__(self) -> Iterator[LogEntry]:
        return iter(self.entries)

    def question_iterator(self) -> "QuestionLogIterator":
        """
        Returns an iterator over the most recent entries for each question.

        Returns:
            ``QuestionLogIterator``: the iterator
        """
        return QuestionLogIterator(self)

    def sort(self, ascending: bool = True):
        """
        Sorts this logs entries by timestamp using ``LogEntry.sort_log``.

        Args:
            ascending (``bool``): whether to sort the log chronologically; defaults to ``True``
        """
        self.entries = LogEntry.sort_log(self.entries, ascending=ascending)
        # self.entries = LogEntry.sort_log(self.entries)
        self.ascending = ascending

    def get_questions(self) -> list[str]:
        """
        Returns a sorted list of all question names that have entries in this log.

        Returns:
            ``list[str]``: the questions in this log
        """
        all_questions = [
            entry.question for entry in self.entries if entry.event_type == EventType.CHECK
        ]
        return list(sorted(set(all_questions)))

    @classmethod
    def from_file(cls, filename: str, ascending: bool = True) -> "Log":
        """
        Loads and sorts a log from a file.

        Args:
            filename (``str``): the path to the log
            ascending (``bool``): whether the log should be sorted in ascending (chronological)
                order; default ``True``

        Returns:
            ``Log``: the ``Log`` instance created from the file
        """
        return cls(
            entries=LogEntry.log_from_file(filename, ascending=ascending), ascending=ascending
        )

    def get_question_entry(self, question: str) -> LogEntry:
        """
        Gets the most recent entry corresponding to the question ``question``

        Args:
            question (``str``): the question to get

        Returns:
            ``LogEntry``: the most recent log entry for ``question``

        Raises:
            ``QuestionNotInLogException``: if the question is not in the log
        """
        if self.ascending:
            self.entries = LogEntry.sort_log(self.entries, ascending=False)
            self.ascending = False
        for entry in self.entries:
            if entry.question == question:
                return entry
        raise QuestionNotInLogException(f"question {question} is not in the log")

    def get_results(self, question: str) -> Optional[Union["GradingResults", "TestFile"]]:
        """Gets the most recent grading result for a specified question from this log

        Args:
            question (``str``): the question name to look up

        Returns:
            ``otter.test_files.GradingResults | otter.test_files.TestFile | None``: the most recent
                result for the question

        Raises:
            ``QuestionNotInLogException``: if the question is not found
        """
        return self.get_question_entry(question).get_results()


class QuestionLogIterator(Iterator[LogEntry]):
    """
    An iterator over the most recent entries for each question in the log. Sorts the log when initialized
    and uses `Log.get_questions` to retrieve the list of questions.

    Args:
        log (``Log``): the log over which to iterate
    """

    log: Log
    """the log being iterated over"""

    questions: list[str]
    """the list of question names"""

    curr_idx: int
    """the integer index of the next question in  ``questions``"""

    def __init__(self, log: Log):
        log.sort(ascending=False)
        log.sort()
        self.log = log
        self.questions = self.log.get_questions()
        self.curr_idx = 0

    def __iter__(self) -> Iterator[LogEntry]:
        return self

    def __next__(self) -> LogEntry:
        if self.curr_idx >= len(self.questions):
            raise StopIteration

        question = self.questions[self.curr_idx]
        entry = self.log.get_question_entry(question)
        self.curr_idx += 1
        return entry


if TYPE_CHECKING:
    from ..test_files import GradingResults, TestFile
