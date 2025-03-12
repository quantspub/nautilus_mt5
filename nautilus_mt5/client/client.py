import os
import asyncio
import functools
from collections.abc import Callable, Coroutine
from inspect import iscoroutinefunction
from typing import Any
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import Component
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.common.enums import LogColor
from nautilus_trader.model.identifiers import ClientId

from nautilus_mt5.constants import MT5_VENUE
from nautilus_mt5.data_types import TerminalConnectionMode
from nautilus_mt5.metatrader5 import RpycConnectionConfig, EAConnectionConfig

class MetaTrader5Client(Component):
    """
    A client component for interfacing with the MetaTrader 5 Terminal.

    This class provides functionality for connection management, account management,
    market data, and order processing with MetaTrader 5. It inherits from `Component`
    to support event-driven responses and custom component behavior.

    It offers an IPC/RPYC/Sockets client for MetaTrader 5.
    """
    def __init__(self,         
                loop: asyncio.AbstractEventLoop,
                msgbus: MessageBus,
                cache: Cache,
                clock: LiveClock,
                mode: TerminalConnectionMode = TerminalConnectionMode.IPC,
                rpyc_config: RpycConnectionConfig = RpycConnectionConfig(),
                ea_config: EAConnectionConfig = EAConnectionConfig(),
                client_id: int = 1,
        ):
        super().__init__(
            clock=clock,
            component_id=ClientId(f"{MT5_VENUE.value}-{client_id:03d}"),
            component_name=f"{type(self).__name__}-{client_id:03d}",
            msgbus=msgbus,
        )

        # Config
        self._loop = loop
        self._cache = cache
        self._mode = mode
        self._rpyc_config = rpyc_config
        self._ea_config = ea_config
        self._client_id = client_id
