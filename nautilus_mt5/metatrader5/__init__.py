import platform
# import importlib.util
import sys
import os
from .config import MetaTrader5Config, RpycConnectionConfig, EAConnectionConfig

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
    "MetaTrader5Config",
    "RpycConnectionConfig",
    "EAConnectionConfig",
]

