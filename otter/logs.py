####################################
##### Logging for Otter-Grader #####
####################################

import os
import pickle
import types
import dill
import tempfile
import datetime as dt
import numpy as np

from enum import Enum, auto
from glob import glob

class QuestionNotInLogException(Exception):
    """Exception that indicates that a specific question was not found in any entry in the log"""


class EventType(Enum):
    """Enum of event types for log entries
    
    Attributes:
        AUTH: an auth event
        BEGIN_CHECK_ALL: beginning of a check-all call
        BEGIN_EXPORT: beginning of an assignment export
        CHECK: a check of a single question
        END_CHECK_ALL: ending of a check-all call
        END_EXPORT: ending of an assignment export
        INIT: initialization of an ``otter.Notebook`` object
        SUBMIT: submission of an assignment
        TO_PDF: PDF export of a notebook
    """

    AUTH = auto()
    BEGIN_CHECK_ALL = auto()
    BEGIN_EXPORT = auto()
    CHECK = auto()
    END_CHECK_ALL = auto()
    END_EXPORT = auto()
    INIT = auto()
    SUBMIT = auto()
    TO_PDF = auto()


class LogEntry:
    """An entry in Otter's log. Tracks event type, grading results, success of operation, and errors
    thrown.

    Args:
        event_type (``otter.logs.EventType``): the type of event for this entry
        results (``list`` of ``otter.ok_parser.OKTestsResult``, optional): the results of grading if 
            this is an ``otter.logs.EventType.CHECK`` record
        question (``str``, optional): the question name for an EventType.CHECK record
        success (``bool``, optional): whether the operation was successful
        error (``Exception``, optional): an error thrown by the process being logged if any

    Attributes:
        event_type (``otter.logs.EventType``): the entry type
        shelf (``bytes``): a pickled environment stored as a bytes string
        unshelved (``list`` of ``str``): a list of variable names that were unable to be pickled during
            shelving
        results (``list`` of ``otter.ok_parser.OKTestsResult``): grading results if this is a check
            entry
        question (``str``): question name if this is a check entry
        success (``bool``): whether the operation tracked by this entry was successful
        error (``Exception``): an error thrown by the tracked process if applicable
        timestamp (``datetime.datetime``): timestamp of event in UTC
    """

    def __init__(self, event_type, shelf=None, unshelved=[], results=[], question=None, success=True, error=None):
        assert event_type in EventType, "Invalid event type"
        self.event_type = event_type
        self.shelf = shelf
        self.unshelved = []
        self.results = results
        self.question = question
        self.timestamp = dt.datetime.utcnow()
        self.success = success
        self.error = error

    def __repr__(self):
        if self.question:
            return "otter.logs.LogEntry(event_type={}, question={}, success={}, timestamp={})".format(
                self.event_type, self.question, self.success, self.timestamp.isoformat()
            )

        return "otter.logs.LogEntry(event_type={}, success={}, timestamp={})".format(
            self.event_type, self.success, self.timestamp.isoformat()
        )

    def get_results(self):
        """Get the results stored in this log entry
        
        Returns:
            ``list`` of ``otter.ok_parser.OKTestsResult``: the results at this entry if this is an 
                ``otter.logs.EventType.CHECK`` record
        """
        assert self.event_type is EventType.CHECK, "this record type has no results"
        if isinstance(self.results, list):
            return self.results[0]
        return self.results

    def get_score_perc(self):
        """Returns the percentage score for the results of this entry

        Returns:
            ``float``: the percentage score
        """
        return self.get_results().grade

    def raise_error(self):
        """Raises the error stored in this entry

        Raises:
            ``Exception``: the error stored at this entry, if present
        """
        if self.error is not None:
            raise self.error

    def flush_to_file(self, filename):
        """Appends this log entry (pickled) to a file
        
        Args:
            filename (``str``): the path to the file to append this entry
        """
        try:
            file = open(filename, "ab+")
            pickle.dump(self, file)

        finally:
            file.close()

    def shelve(self, env, delete=False, filename=None, ignore_modules=[], variables=None):
        """
        Stores an environment ``env`` in this log entry using dill as a ``bytes`` object in this entry
        as the ``shelf`` attribute. Writes names of any variables in ``env`` that are not stored to
        the ``unshelved`` attribute.

        If ``delete`` is ``True``, old environments in the log at ``filename`` for this question are
        cleared before writing ``env``. Any module names in ``ignore_modules`` will have their functions
        ignored during pickling.

        Args:
            env (``dict``): the environment to pickle
            delete (``bool``, optional): whether to delete old environments
            filename (``str``, optional): path to log file; ignored if ``delete`` is ``False``
            ignore_modules (``list`` of ``str``, optional): module names to ignore during pickling
            variables (``dict``, optional): map of variable name to type string indicating **only** 
                variables to include (all variables not in this dictionary will be ignored)

        Returns:
            ``otter.logs.LogEntry``: this entry
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
                            entry = pickle.load(tf)

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
                variables = {k : v for k, v in variables.items() if k in variables_stored}
        except UnboundLocalError:
            pass

        shelf_contents, unshelved = LogEntry.shelve_environment(env, variables=variables, ignore_modules=ignore_modules)
        self.shelf = shelf_contents
        self.unshelved = unshelved
        return self
        
    def unshelve(self, global_env={}):
        """
        Parses a ``bytes`` object stored in the ``shelf`` attribute and unpickles the object stored
        there using dill. Updates the ``__globals__`` of any functions in ``shelf`` to include elements
        in the shelf. Optionally includes the env passed in as ``global_env``.

        Args:
            global_env (``dict``, optional): a global env to include in unpickled function globals

        Returns:
            ``dict``: the shelved environment
        """
        assert self.shelf, "no shelf in this entry"

        # read bytes in self.shelf and load with dill
        with tempfile.TemporaryFile() as tf:
            tf.write(self.shelf)
            tf.seek(0)
            shelf = dill.load(tf)
            
        # add the unpickeld env and global_env to all function __globals__
        for k, v in shelf.items():
            if type(v) == types.FunctionType:
                v.__globals__.update(shelf)
                v.__globals__.update(global_env)

        return shelf

    @staticmethod
    def sort_log(log, ascending=True):
        """Sorts a list of log entries by timestamp
        
        Args:
            log (``list`` of ``otter.logs.LogEntry``): the log to sort
            ascending (``bool``, optional): whether the log should be sorted in ascending (chronological) 
                order; default ``True``

        Returns:
            ``list`` of ``otter.logs.LogEntry``: the sorted log
        """
        if ascending:
            return list(sorted(log, key = lambda l: l.timestamp))
        return list(sorted(log, key = lambda l: l.timestamp, reverse = True))

    @staticmethod
    def log_from_file(filename, ascending=True):
        """Reads a log file and returns a sorted list of the log entries pickled in that file
        
        Args:
            filename (``str``): the path to the log
            ascending (``bool``, optional): whether the log should be sorted in ascending (chronological) 
                order; default ``True``

        Returns:
            ``list`` of ``otter.logs.LogEntry``: the sorted log
        """
        try:
            file = open(filename, "rb")

            log = []
            while True:
                try:
                    log.append(pickle.load(file))
                except EOFError:
                    break

            log = list(sorted(log, key = lambda l: l.timestamp, reverse = not ascending))
            
            return log
            
        finally:
            file.close()

    @staticmethod
    def shelve_environment(env, variables=None, ignore_modules=[]):
        """
        Pickles an environment ``env`` using dill, ignoring any functions whose module is listed in
        ``ignore_modules``. Returns the pickle file contents as a ``bytes`` object and a list of
        variable names that were unable to be shelved/ignored during shelving.

        Args:
            env (``dict``): the environment to shelve
            variables (``dict`` *or* ``list``, optional): a map of variable name to type string indicating 
                **only** variables to include (all variables not in this dictionary will be ignored) 
                or a list of variable names to include regardless of tpye
            ignore_modules (``list`` of ``str``, optional): the module names to igonre

        Returns:
            ``tuple`` of (``bytes``, ``list`` of ``str``): the pickled environment and list of unshelved
                variable names.
        """
        from .notebook import Notebook
        unshelved = []
        filtered_env = {}
        for k, v in env.items():

            # don't store modules or otter.Notebook instances
            if type(v) == types.ModuleType or type(v) == Notebook:
                unshelved.append(k)
            
            # ignore any functions whose __module__ is in ignore_modules
            elif type(v) == types.FunctionType and v.__module__ in ignore_modules:
                unshelved.append(k)
            
            # ensure object is pickleable by attempting dump and if so add to filtered_env
            else:
                try:
                    dill.dumps(v)

                    # only store variable names in variables that have the correct type
                    if (variables and k in variables) or not variables:
                        full_type = type(v).__module__ + "." + type(v).__name__

                        if (isinstance(variables, dict) and full_type == variables[k]) or \
                            isinstance(variables, list) or not variables:
                            filtered_env[k] = v

                        else:
                            unshelved.append(k)

                    else:
                        unshelved.append(k)
                        
                except:
                    unshelved.append(k)

        # dump filtered_env to a temporary file and then return the bytes and unshelved list
        with tempfile.TemporaryFile() as tf:
            dill.dump(filtered_env, tf)
            tf.seek(0)
            shelf_contents = tf.read()
            
        return shelf_contents, unshelved


class Log:
    """
    A class for reading and interacting with a log. Allows you to iterate over the entries in the log 
    and supports integer indexing. *Does not support editing the log file.*

    Args:
        entries (``list`` of ``otter.logs.LogEntry``): the list of entries for this log
        ascending (``bool``, optional): whether the log is sorted in ascending (chronological) order;
            default ``True``

    Attributes:
        entries (``list`` of ``otter.logs.LogEntry``): the list of log entries in this log
        ascending (``bool``): whether ``entries`` is sorted chronologically; ``False`` indicates reverse-
            chronological order
    """

    def __init__(self, entries, ascending=True):
        self.entries = entries
        self.ascending = ascending

    def __repr__(self):
        return "otter.logs.Log([\n  {}\n])".format(",\n  ".join([repr(e) for e in self.entries]))

    def __getitem__(self, idx):
        return self.entries[idx]

    def __iter__(self):
        return iter(self.entries)

    def question_iterator(self):
        """
        Returns an iterator over the most recent entries for each question.

        Returns:
            ``otter.logs.QuestionLogIterator``: the iterator
        """
        return QuestionLogIterator(self)

    def sort(self, ascending=True):
        """
        Sorts this logs entries by timestmap using ``otter.logs.LogEntry.sort_log``.

        Args:
            ascending (``bool``, optional): whether to sort the log chronologically; defaults to ``True``
        """
        self.entries = LogEntry.sort_log(self.entries, ascending=ascending)
        self.ascending = ascending

    def get_questions(self):
        """
        Returns a sorted list of all question names that have entries in this log.

        Returns:
            ``list`` of ``str``: the questions in this log
        """
        all_questions = [entry.question for entry in self.entries if entry.event_type == EventType.CHECK]
        return list(sorted(set(all_questions)))

    @classmethod
    def from_file(cls, filename, ascending=True):
        """Loads and sorts a log from a file.

        Args:
            filename (``str``): the path to the log
            ascending (``bool``, optional): whether the log should be sorted in ascending (chronological) 
                order; default ``True``

        Returns:
            ``otter.logs.Log``: the ``Log`` instance created from the file
        """
        return cls(entries=LogEntry.log_from_file(filename, ascending=ascending), ascending=ascending)

    def get_question_entry(self, question):
        """
        Gets the most recent entry corresponding to the question ``question``

        Args:
            question (``str``): the question to get

        Returns:
            ``otter.logs.LogEntry``: the most recent log entry for ``question``
        
        Raises:
            ``otter.logs.QuestionNotInLogException``: if the question is not in the log
        """
        if self.ascending:
            self.entries = LogEntry.sort_log(self.entries, ascending=False)
            self.ascending = False
        for entry in self.entries:
            if entry.question == question:
                return entry
        raise QuestionNotInLogException(f"question {question} is not in the log")

    def get_results(self, question):
        """Gets the most recent grading result for a specified question from this log

        Args:
            question (``str``): the question name to look up

        Returns:
            ``otter.ok_parser.OKTestsResult``: the most recent result for the question

        Raises:
            ``otter.logs.QuestionNotInLogException``: if the question is not found
        """
        return self.get_question_entry(question).get_results()

class QuestionLogIterator:
    """
    An iterator over the most recent entries for each question in the log. Sorts the log when initialized
    and uses `Log.get_questions` to retrieve the list of questions.

    Args:
        log (``otter.logs.Log``): the log over which to iterate

    Attributes:
        log (``otter.logs.Log``): the log being iterated over
        questions (``list`` of ``str``): the list of question names
        curr_idx (``int``): the integer index of the next question in  ``questions``
    """
    def __init__(self, log):
        log.sort(ascending=False)
        self.log = log
        self.questions = self.log.get_questions()
        self.curr_idx = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.curr_idx >= len(self.questions):
            raise StopIteration

        question = self.questions[self.curr_idx]
        entry = self.log.get_question_entry(question)
        self.curr_idx += 1
        return entry
