"""
MetaTrader5 EA package.

EA Sockets Prototype Folder.
"""
from nautilus_mt5.metatrader5.ea.client import EAClientConfig, EAClient
from nautilus_mt5.metatrader5.ea.connection import Connection
from nautilus_mt5.metatrader5.ea.errors import ERROR_DICT
from nautilus_mt5.metatrader5.ea.models import *
from nautilus_mt5.metatrader5.ea.utils import *

# try:
#     from nautilus_mt5.metatrader5.ea.data_stream import MetaTrader5Streamer

#     # TODO: Switch Streaming core to MQTT:
#     # https://github.com/eclipse-paho/paho.mqtt.python/
#     # https://en.wikipedia.org/wiki/MQTT
# except ImportError as e:
#     raise ImportError(
#         "Failed to import MetaTrader5Streamer. Ensure that data_stream file exists in the nautilus_mt5.metatrader5 directory and is properly compiled."
#     ) from e


__all__ = [
    "EAClientConfig",
    "EAClient",
    "Connection",
    "ERROR_DICT",
    # "MetaTrader5Streamer",
]

"""
low level messaging protocol for financial data streaming.

use sockets
use a custom protocol not FIX
use a custom message format not JSON
"""