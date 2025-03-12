import platform

# import importlib.util
import sys
import os
from .errors import *

current_dir = os.path.dirname(__file__)
try:
    if platform.system() == "Windows":
        import MetaTrader5 as MetaTrader5

        # MetaTrader5 = importlib.import_module("MetaTrader5")
    else:
        sys.path.insert(0, current_dir)
        try:
            from . import MetaTrader5 as MetaTrader5

            # MetaTrader5 = importlib.import_module(
            #     ".MetaTrader5", package="metatrader5ext"
            # )
        except ImportError:
            raise ImportError("MetaTrader5 is not available on this system.")
except ImportError as e:
    raise ImportError(f"Failed to import MetaTrader5: {e}")
finally:
    if current_dir in sys.path:
        sys.path.remove(current_dir)


try:
    from nautilus_mt5.metatrader5.terminal import (
        ContainerStatus,
        DockerizedMT5TerminalConfig,
        DockerizedMT5Terminal,
        ContainerExists,
        NoContainer,
        UnknownContainerStatus,
        TerminalLoginFailure,
    )
except ImportError as e:
    raise ImportError(
        "Failed to import DockerizedMT5Terminal. Ensure that terminal file exists"
    ) from e

__all__ = [
    "MetaTrader5",
    "RpycConfig",
    "DockerizedMT5TerminalConfig",
    "DockerizedMT5Terminal",
    "ContainerStatus",
    "ContainerExists",
    "NoContainer",
    "UnknownContainerStatus",
    "TerminalLoginFailure",
]



# from rpyc.utils.classic import DEFAULT_SERVER_PORT as RPYC_DEFAULT_SERVER_PORT
# from mt5.metatrader5 import MetaTrader5, RpycConfig, DockerizedMT5Terminal, DockerizedMT5TerminalConfig
# from metatrader5ext.ea import EAClient, EAClientConfig
# from mt5.metatrader5ext import MetaTrader5Ext, MetaTrader5ExtConfig
# from mt5.timeframe_agg import TimeframeAggregator
# from mt5.logging import Logger as MTLogger
# from nautilus_mt5.metatrader5.common import *
# from nautilus_mt5.metatrader5.errors import *

# __all__ = [
#     "MetaTrader5ExtConfig",
#     "MetaTrader5Ext",
#     "DockerizedMT5TerminalConfig",
#     "DockerizedMT5Terminal",
#     "RpycConfig",
#     "MetaTrader5",
#     "EAClient",
#     "TimeframeAggregator",
#     "MTLogger",
#     "RPYC_DEFAULT_SERVER_PORT",
# ]
