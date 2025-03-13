from decimal import Decimal
from typing import Final
from nautilus_trader.model.identifiers import Venue

from nautilus_mt5.client.types import ErrorInfo
from nautilus_mt5.metatrader5 import MetaTrader5

MT5_VENUE: Final[Venue] = Venue("METATRADER_5")
NO_VALID_ID = -1
UNSET_DECIMAL = Decimal(2**127 - 1)

ALREADY_CONNECTED = ErrorInfo(1, "Already connected.")
RPYC_SERVER_CONNECT_FAIL = ErrorInfo(-1, "Rpyc Server connection failed")
TERMINAL_CONNECT_FAIL = ErrorInfo(0, "Terminal connection failed")
TERMINAL_INIT_FAIL = ErrorInfo(MetaTrader5.RES_E_INTERNAL_FAIL_INIT, "MetaTrader5 instance is not initialized")
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