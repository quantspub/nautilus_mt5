class TerminalError(Exception):
    pass

class SymbolSelectError(Exception):
    pass

class ErrorInfo:
    """Class to represent an error with a code and message."""
    
    def __init__(self, code: int, msg: str):
        self._code = code
        self._msg = msg

    def __str__(self) -> str:
        return f"ErrorInfo(code={self._code}, msg={self._msg})"

    def code(self) -> int:
        """Returns the error code."""
        return self._code

    def msg(self) -> str:
        """Returns the error message."""
        return self._msg

ALREADY_CONNECTED = ErrorInfo(1, "Already connected.")
RPYC_SERVER_CONNECT_FAIL = ErrorInfo(-1, "Rpyc Server connection failed")
TERMINAL_CONNECT_FAIL = ErrorInfo(-10003, "Terminal initialization failed")
UPDATE_TERMINAL = ErrorInfo(503, "The TERMINAL is out of date and must be upgraded.")
NOT_CONNECTED = ErrorInfo(504, "Not connected")
UNKNOWN_ID = ErrorInfo(505, "Fatal Error: Unknown message id.")
UNSUPPORTED_VERSION = ErrorInfo(506, "Unsupported version")
BAD_LENGTH = ErrorInfo(507, "Bad message length")
BAD_MESSAGE = ErrorInfo(508, "Bad message")
SOCKET_EXCEPTION = ErrorInfo(509, "Exception caught while reading socket - ")
FAIL_CREATE_SOCK = ErrorInfo(520, "Failed to create socket")
SSL_FAIL = ErrorInfo(530, "SSL specific error: ")
INVALID_SYMBOL = ErrorInfo(579, "Invalid symbol in string - ")
