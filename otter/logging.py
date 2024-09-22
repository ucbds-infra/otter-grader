import logging
import logging.handlers

from contextlib import contextmanager
from multiprocessing import Queue
from typing import Optional


ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG


_instances: dict[str, logging.Logger] = {}
"""all ``logging.Logger`` instances by name"""

_log_level: int = logging.WARNING
"""the current log level"""

_handler = logging.StreamHandler()
"""the formatter to use when formatting log records"""

_handlers: list[logging.Handler] = [_handler]
"""extra handlers that should receive logs"""


# set a formatter on _handler
_handler.setFormatter(logging.Formatter("[%(levelname)s %(name)s.%(funcName)s] %(message)s"))


def send_logs(host: str, port: int):
    """
    Add a ``SocketHandler`` to all loggers that sends their logs to a TCP socket at the
    specified host and port.
    """
    socket_handler = logging.handlers.SocketHandler(host, port)
    _handlers.append(socket_handler)
    for logger in _instances.values():
        logger.addHandler(socket_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve ``logging.Logger`` with name ``name`` and return it, setting the log level to the
    class log level.
    """
    if name in _instances:
        return _instances[name]

    logger = logging.getLogger(name)
    logger.propagate = False  # prevent child loggers from inheriting the handler
    logger.setLevel(_log_level)

    for h in _handlers:
        logger.addHandler(h)

    _instances[name] = logger
    return logger


def _get_queue_handler() -> Optional["QueueLoggingHandler"]:
    for h in _handlers:
        if isinstance(h, QueueLoggingHandler):
            return h
    return None


def add_queue_handler(result_queue: "Queue[str]"):
    """
    Set up a ``QueueLoggingHandler`` that sends all logged messages to the provided
    ``multiprocessing.Queue``.

    Args:
        result_queue (``multiprocessing.Queue[str]``): the queue to write logs to
    """
    if _get_queue_handler() is not None:
        raise RuntimeError("A QueueLoggingHandler is already set up")

    queue_handler = QueueLoggingHandler(result_queue)
    _handlers.append(queue_handler)
    for logger in _instances.values():
        logger.addHandler(queue_handler)


def remove_queue_handlers():
    """
    Remove the current ``QueueLoggingHandler`` if one is set up.
    """
    qh = _get_queue_handler()
    if qh is None:
        return
    for logger in _instances.values():
        logger.removeHandler(qh)
    _handlers.remove(qh)


def get_level() -> int:
    """
    Return the current log level of these loggers.
    """
    return _log_level


def set_level(log_level: int):
    """
    Set the log levels for all ``Logger``s created by this class (existing and future).
    """
    global _log_level
    _log_level = log_level
    for logger in _instances.values():
        logger.setLevel(log_level)


@contextmanager
def level_context(log_level: int):
    """
    Set the log level to a new value temporarily in a context.
    """
    curr_level = get_level()
    set_level(log_level)
    yield
    set_level(curr_level)


def reset_level():
    """
    Set the log levels for all ``Loggers`` created by this class (existing and future) back to
    ``logging.WARNING``.
    """
    set_level(logging.WARNING)


class Loggable:
    """
    A class for inheriting from that provides a logger via a class- and instance-accessible field.
    """

    _logger_instance: Optional[logging.Logger] = None

    @classmethod
    def _load_logger(cls):
        """
        Set-up the ``_logger`` field.
        """
        if cls._logger_instance is None:
            name = cls.__module__ + "." + cls.__name__
            cls._logger_instance = get_logger(name)

    @property
    def _logger(self) -> logging.Logger:
        """
        ``logging.Logger``: the logger instance for this class
        """
        return self._get_logger()

    @classmethod
    def _get_logger(cls) -> logging.Logger:
        """
        Load and return the logger for this class.

        Returns:
            ``logging.Logger``: the logger instance for this class
        """
        cls._load_logger()
        return cls._logger_instance


class QueueLoggingHandler(logging.Handler):
    """The logging handler that writes INFO messages to the log_queue.

    Args:
        log_queue (``multiprocessing.Queue``): the queue this handler writes to
    """

    def __init__(self, log_queue: "Queue[str]"):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord):
        try:
            log_entry = self.format(record)
            self.log_queue.put(log_entry)
        except Exception:
            self.handleError(record)
