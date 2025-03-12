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
    
class TerminalPlatformType(Enum):
    """Terminal Platform type.
    
    Includes 2 platform types: WINDOWS and LINUX.
    """
    WINDOWS = "Windows"
    LINUX = "Linux"

    def to_str(self) -> str:
        """Returns the string representation of the enum value."""
        return self.value