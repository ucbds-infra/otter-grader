####################################
##### Logging for Otter-Grader #####
####################################

import re
import os
import pickle
import shelve
import types
import dill
import tempfile
import datetime as dt

from enum import Enum, auto
from glob import glob


_SHELF_FILENAME = ".OTTER_ENV"


class QuestionNotInLogException(Exception):
    """Exception that indicates that a specific question was not found in any entry in the log"""


class EventType(Enum):
    """Event types for log entries"""

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

    def raise_error(self):
        """Raises the error stored in this entry

        Raises:
            ``Exception``: the error stored at this entry, if present
        """
        if self.error is not None:
            raise self.error
        # raise ValueError("No error is stored in this log entry")

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

    def shelve(self, env, delete=False, filename=None):
        # delete old entry without reading entire log
        if delete:
            assert filename, "old env deletion indicated but no log filename provided"
            try:
                entries = []
                os.system(f"cp {filename} .TEMP_LOG")
                os.system(f"rm -f {filename}")
                with open(".TEMP_LOG", "rb") as tf:
                    while True:
                        try:
                            entry = pickle.load(tf)

                            if entry.question == self.question:
                                entry.shelf = None

                            entry.flush_to_file(filename)

                            del locals()["entry"]

                        except EOFError:
                            break
                os.system("rm -f .TEMP_LOG")

            except FileNotFoundError:
                pass

        shelf_contents, unshelved = LogEntry.shelve_environment(env)
        self.shelf = shelf_contents
        self.unshelved = unshelved
        return self
        
    def unshelve(self):
        assert self.shelf, "no shelf in this entry"
        # for ext in self.shelf:
        #     with open(_SHELF_FILENAME + ext, "wb+") as f:
        #         f.write(self.shelf[ext])
        
        # shelf = shelve.open(_SHELF_FILENAME)
        with tempfile.TemporaryFile() as tf:
            tf.write(self.shelf)
            shelf = dill.load(tf)

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
    def shelve_environment(env):
        unshelved = []
        filtered_env = {}
        for k, v in env.items():
            if type(k) == types.ModuleType:
                unshelved.append(k)
            else:
                filtered_env[k] = v

        # with shelve.open(_SHELF_FILENAME) as shelf:
        #     for k, v in env.items():
        #         if type(v) == types.ModuleType:
        #             continue
        #         try:
        #             shelf[k] = v
        #         except:
        #             unshelved.append(k)
        
        # shelf_files = {}
        # for file in glob(_SHELF_FILENAME + "*"):
        #     ext = re.sub(_SHELF_FILENAME, "", file)
        #     f = open(file, "rb")
        #     shelf_files[ext] = f.read()
        #     f.close()

        with tempfile.TemporaryFile() as tf:
            dill.dump(filtered_env, tf)
            shelf_contents = tf.read()
            
        return shelf_contents, unshelved


class Log:
    """A class for reading and interacting with a log. *Does not support editing the log file.*

    Args:
        entries (``list`` of ``otter.logs.LogEntry``): the list of entries for this log
        ascending (``bool``, optional): whether the log is sorted in ascending (chronological) order;
            default ``True``
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
        return QuestionLogIterator(self)

    def sort(self, ascending=True):
        self.entries = LogEntry.sort_log(self.entries, ascending=ascending)
        self.ascending = ascending

    def get_questions(self):
        all_questions = [entry.question for entry in self.entries if entry.event_type == EventType.CHECK]
        return list(sorted(set(all_questions)))

    @classmethod
    def from_file(cls, filename, ascending=True):
        """Loads a log from a file

        Args:
            filename (``str``): the path to the log
            ascending (``bool``, optional): whether the log should be sorted in ascending (chronological) 
                order; default ``True``

        Returns:
            ``otter.logs.Log``: the ``Log`` instance created from the file
        """
        return cls(entries=LogEntry.log_from_file(filename, ascending=ascending), ascending=ascending)

    def get_question_entry(self, question):
        if self.ascending:
            self.entries = LogEntry.sort_log(self.entries)
            self.ascending = False
        for entry in self.entries:
            if entry.question == question:
                return entry
        raise QuestionNotInLogException()

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
