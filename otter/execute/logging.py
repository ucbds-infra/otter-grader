"""A logging server for receiving logs from the grading process"""

import logging
import logging.handlers
import pickle
import socket
import socketserver
import struct
import threading

from ..logging import get_level, get_logger


LOGGER = get_logger(__name__)


class LogLevelFilter(logging.Filter):
    """
    A simple ``logging.Filter`` that checks that the level of the provided ``LogRecord`` is at least
    as high as the configured log level.
    """

    def filter(self, record: logging.LogRecord):
        return record.levelno >= get_level()


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """
    A handler for a streaming logging request.

    Copied from https://docs.python.org/3/howto/logging-cookbook.html#sending-and-receiving-logging-events-across-a-network.
    """

    filter = LogLevelFilter()

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unpickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handle_log_record(record)

    def unpickle(self, data: bytes):
        return pickle.loads(data)

    def handle_log_record(self, record: logging.LogRecord):
        logger = get_logger(record.name)
        if self.filter.filter(record):
            logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver.

    Copied from https://docs.python.org/3/howto/logging-cookbook.html#sending-and-receiving-logging-events-across-a-network.
    """

    allow_reuse_address = True
    abort = False

    def __init__(
        self,
        host: str = "localhost",
        port: int = 0,
        handler: type[logging.Handler] = LogRecordStreamHandler,
    ):
        super().__init__((host, port), handler)

    def serve_until_stopped(self):
        import select

        abort = False
        while not abort:
            rd = None
            try:
                rd, _, _ = select.select([self.socket.fileno()], [], [], 1)
            except socket.error:
                pass
            if rd:
                self.handle_request()
            abort = self.abort


def start_server():
    """
    Start a TCP socket for receiving logs from the notebook being executed. Returns a tuple of
    ``((server host, server port), stop server callback)``.

    Returns:
        ``tuple[tuple[str, int], callable]``: a tuple containing a tuple with the server host and
            port as its first element and a callback to stop the server as its second
    """
    tcpserver = LogRecordSocketReceiver()
    host, port = tcpserver.server_address
    LOGGER.debug(f"Starting execution logging TCP server in background at {host}:{port}")
    t = threading.Thread(target=tcpserver.serve_until_stopped)
    t.start()

    def stop_server():
        LOGGER.debug("Stopping execution logging TCP server")
        tcpserver.abort = True

    return tcpserver.server_address, stop_server
