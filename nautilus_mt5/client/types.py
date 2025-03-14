from enum import Enum

class SubscriptionStatus(Enum):
    """
    Represents a MetaTrader subscription status.
    """

    UNSUBSCRIBED = 0
    PENDING_STARTUP = 1
    RUNNING = 2
    SUBSCRIBED = 3

class MarketDataSubscription(Enum):
    """
    Represents a MetaTrader market data subscription.
    """

    DELAYED = 0
    REALTIME = 1

class TerminalConnectionState(Enum):
    """
    Represents a MetaTrader terminal connection state.
    """

    DISCONNECTED = 0
    CONNECTED = 1
    CONNECTING = 2
    REDIRECTED = 3
    
class TerminalConnectionMode(Enum):
    """Terminal Connection Mode type.
    
    Includes 3 client modes: IPC, EA, and EA_IPC.

    IPC: Mode for MetaTrader IPC communication on Windows.
    EA: Mode for EA communication using sockets.
    EA_IPC: Mode for combining EA and IPC communication (EA for streaming and IPC for request-reply).
    
    Since RPYC is used for IPC communication in Linux, it will be used for IPC mode in Linux (MetaTrader RPYC communication on Linux).
    """
    IPC = "IPC"
    EA = "EA"
    EA_IPC = "EA_IPC"

    def to_str(self) -> str:
        """Returns the string representation of the enum value."""
        return self.value
    
class TerminalPlatform(Enum):
    """Terminal Platform type.
    
    Includes 2 platform types: WINDOWS and LINUX.
    """
    WINDOWS = "Windows"
    LINUX = "Linux"

    def to_str(self) -> str:
        """Returns the string representation of the enum value."""
        return self.value
    
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