import os
import asyncio
import functools
from collections.abc import Callable, Coroutine
from inspect import iscoroutinefunction
from typing import Any, Dict, Optional, Union
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import Component
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.common.enums import LogColor
from nautilus_trader.model.identifiers import ClientId

from nautilus_mt5.metatrader5 import RpycConnectionConfig, EAConnectionConfig
from nautilus_mt5.client import TerminalConnectionMode
from nautilus_mt5.client.account import MetaTrader5ClientAccountMixin
from nautilus_mt5.client.connection import MetaTrader5ClientConnectionMixin
from nautilus_mt5.constants import MT5_VENUE


class MetaTrader5Client(Component,
                        MetaTrader5ClientConnectionMixin,
                        MetaTrader5ClientAccountMixin,):
    """
    A client component for interfacing with the MetaTrader 5 Terminal.

    This class provides functionality for connection management, account management,
    market data, and order processing with MetaTrader 5. It inherits from `Component`
    to support event-driven responses and custom component behavior.

    It offers an IPC/RPYC/Sockets client for MetaTrader 5.

    In EA_IPC mode, it uses IPC/RPYC for request-reply and EA Sockets for streaming.
    """
    def __init__(self,         
                loop: asyncio.AbstractEventLoop,
                msgbus: MessageBus,
                cache: Cache,
                clock: LiveClock,
                connection_mode: TerminalConnectionMode = TerminalConnectionMode.IPC,
                mt5_config: Dict[str, Optional[Union[RpycConnectionConfig, EAConnectionConfig]]] = {
                    "rpyc": RpycConnectionConfig(),
                    "ea": EAConnectionConfig(),
                },
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
        self._terminal_connection_mode = connection_mode
        self._mt5_config = mt5_config
        self._client_id = client_id

    def _start(self) -> None:
        """
        Start the client.

        This method is called when the client is first initialized and when the client
        is reset. It sets up the client and starts the connection watchdog, incoming
        message reader, and internal message queue processing tasks.

        """
        if not self._loop.is_running():
            self._log.warning("Started when loop is not running.")
            self._loop.run_until_complete(self._start_async())
        else:
            self._create_task(self._start_async())
    
    def _stop(self) -> None:
        """
        Stop the client and cancel running tasks.
        """
        self._create_task(self._stop_async())
