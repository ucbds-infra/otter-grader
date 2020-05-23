
#####  #####

import pickle
import datetime as dt

from enum import Enum, auto


class EventType(Enum):
    """
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
    """
    """

    def __init__(self, event_type, results=[], question=None, success=True, error=None):
        assert event_type in EventType
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
        return self.results

    def get_question_results(self, question):
        assert self.event_type is EventType.CHECK
        assert question == self.question, "question {} not in this log entry".format(question)
        if isinstance(self.results, list):
            return self.results[0]
        return self.results

    def flush_to_file(self, filename):
        try:
            file = open(filename, "ab+")
            pickle.dump(self, file)

        finally:
            file.close()

    @staticmethod
    def log_from_file(filename, ascending=True):
        """Returns list of log entries"""
        try:
            file = open(filename, "rb")

            log = []
            while True:
                try:
                    log.append(pickle.load(file))
                except EOFError:
                    break

            if not ascending:
                log = list(sorted(log, key = lambda l: l.timestamp, reverse = True))
            
            return log
            
        finally:
            file.close()
        