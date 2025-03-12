import platform
# import importlib.util
import sys
import os
from nautilus_mt5.metatrader5.config import RpycConnectionConfig, EAConnectionConfig
from nautilus_mt5.metatrader5.ea_client import EAClient
from nautilus_mt5.metatrader5.ea_sockets import EASocketConnection 
from nautilus_mt5.metatrader5.errors import *
from nautilus_mt5.metatrader5.models import *
from nautilus_mt5.metatrader5.utils import *

current_dir = os.path.dirname(__file__)
try:
    if platform.system() == "Windows":
        import MetaTrader5 as MetaTrader5

        # MetaTrader5 = importlib.import_module("MetaTrader5")
    else:
        sys.path.insert(0, current_dir)
        try:
            from .MetaTrader5 import MetaTrader5 as MetaTrader5

            # MetaTrader5 = importlib.import_module(
            #     ".MetaTrader5", package="nautilus_mt5"
            # )
        except ImportError:
            raise ImportError("MetaTrader5 is not available on this system.")
except ImportError as e:
    raise ImportError(f"Failed to import MetaTrader5: {e}")
finally:
    if current_dir in sys.path:
        sys.path.remove(current_dir)


__all__ = [
    "MetaTrader5",
    "RpycConnectionConfig",
    "EAConnectionConfig",
    "EAClient",
    "EASocketConnection",
    "ERROR_DICT",
]




"""
low level messaging protocol for financial data streaming.

use sockets
use a custom protocol not FIX
use a custom message format not JSON
"""