####################################
##### Logging for Otter-Grader #####
####################################

import pickle
import datetime as dt

from enum import Enum, auto


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

    def __init__(self, event_type, results=[], question=None, success=True, error=None):
        assert event_type in EventType, "Invalid event type"
        self.event_type = event_type
        self.results = results
        self.question = question
        self.timestamp = dt.datetime.utcnow()
        self.success = success
        self.error = error

    def __repr__(self):
        if self.question:
            return "otter.logs.LogEntry(event_type={}, question={}, sucess={}, timestamp={})".format(
                self.event_type, self.question, self.success, self.timestamp.isoformat()
            )

        return "otter.logs.LogEntry(event_type={}, sucess={}, timestamp={})".format(
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

            if ascending:
                log = list(sorted(log, key = lambda l: l.timestamp))
            else:
                log = list(sorted(log, key = lambda l: l.timestamp, reverse = True))
            
            return log
            
        finally:
            file.close()

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

    def get_results(self, question):
        """Gets the most recent grading result for a specified question from this log

        Args:
            question (``str``): the question name to look up

        Returns:
            ``otter.ok_parser.OKTestsResult``: the most recent result for the question

        Raises:
            ``otter.logs.QuestionNotInLogException``: if the question is not found
        """
        if self.ascending:
            self.entries = LogEntry.sort_log(self.entries)
            self.ascending = False
        for entry in self.entries:
            if entry.question == question:
                return entry.get_results()
        raise QuestionNotInLogException()
