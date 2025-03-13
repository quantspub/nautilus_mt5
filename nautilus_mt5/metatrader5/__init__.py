import platform
import sys
import os
from contextlib import suppress
from nautilus_mt5.metatrader5.config import RpycConnectionConfig, EAConnectionConfig
from nautilus_mt5.metatrader5.ea_client import EAClient
from nautilus_mt5.metatrader5.ea_sockets import EASocketConnection
from nautilus_mt5.metatrader5.errors import EA_ERROR_DICT
from nautilus_mt5.metatrader5.models import *
from nautilus_mt5.metatrader5.utils import *

current_dir = os.path.dirname(__file__)

with suppress(ImportError):
    if platform.system() == "Windows":
        import MetaTrader5
    else:
        sys.path.insert(0, current_dir)
        try:
            from .MetaTrader5 import MetaTrader5
        finally:
            sys.path.remove(current_dir)

if "MetaTrader5" not in sys.modules:
    raise ImportError("MetaTrader5 is not available on this system.")

__all__ = [
    "MetaTrader5",
    "RpycConnectionConfig",
    "EAConnectionConfig",
    "EAClient",
    "EASocketConnection",
    "EA_ERROR_DICT",
]

"""
Low-level messaging protocol for financial data streaming.

- Uses sockets.
- Implements a custom protocol (not FIX).
- Uses a custom message format (not JSON).
"""
