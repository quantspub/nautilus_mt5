import asyncio
import platform
from datetime import datetime
from typing import Dict, Union
from nautilus_trader.common.enums import LogColor

from nautilus_mt5.constants import NO_VALID_ID, TERMINAL_CONNECT_FAIL
from nautilus_mt5.metatrader5 import MetaTrader5, EAClient
from nautilus_mt5.common import BaseMixin
from nautilus_mt5.client.types import (
    ErrorInfo,
    TerminalConnectionMode,
    TerminalConnectionState,
    TerminalPlatform,
)


class MetaTrader5ClientConnectionMixin(BaseMixin):
    """
    Manages the connection to MetaTrader 5 Terminal.
    """

    async def _connect(self) -> None:
        """Establish the connection with Terminal."""
        self._terminal_platform = TerminalPlatform(platform.system().capitalize())
        self.set_conn_state(TerminalConnectionState.CONNECTING)
        
        try:
            await self._initialize_and_connect()
            await self._fetch_terminal_info()
            self.set_conn_state(TerminalConnectionState.CONNECTED)
            self._log_connection_info()
        except asyncio.CancelledError:
            self._log.info("Connection cancelled.")
            await self._disconnect()
        except Exception as e:
            self._log.error(f"Connection failed: {e}")
            self._handle_connection_error()
            await self._handle_reconnect()

    async def _disconnect(self) -> None:
        """Disconnect from Terminal and clear connection flag."""
        try:
            self._clear_clients()
            self.set_conn_state(TerminalConnectionState.DISCONNECTED)
            if self._is_mt5_connected.is_set():
                self._log.debug("_is_mt5_connected unset by _disconnect.", LogColor.BLUE)
                self._is_mt5_connected.clear()
            self._log.info("Disconnected from MetaTrader 5 Terminal.")
        except Exception as e:
            self._log.error(f"Disconnection failed: {e}")

    async def _handle_reconnect(self) -> None:
        """Attempt to reconnect to Terminal."""
        self._reset()
        self._resume()

    async def _initialize_and_connect(self) -> None:
        """Initialize connection parameters and establish connection."""
        await asyncio.to_thread(self._create_mt5_client)
        if self._mt5_client['mt5']:
            self._mt5_client['mt5'].id = self._client_id
        if self._mt5_client['ea']:
            self._mt5_client['ea'].id = self._client_id

    def _create_mt5_client(self) -> Dict[str, Union[MetaTrader5, EAClient]]:
        """Create and return the appropriate MetaTrader5 client."""
        clients = {'mt5': None, 'ea': None}
        if self._terminal_connection_mode == TerminalConnectionMode.IPC:
            clients['mt5'] = self._create_ipc_client()
        elif self._terminal_connection_mode == TerminalConnectionMode.EA:
            clients['ea'] = self._create_ea_client()
        elif self._terminal_connection_mode == TerminalConnectionMode.EA_IPC:
            clients.update(self._create_ea_ipc_client())
        else:
            raise ValueError(f"Invalid connection mode: {self._terminal_connection_mode}")
        return clients

    def _create_ipc_client(self) -> MetaTrader5:
        """Create an IPC-based MetaTrader5 client."""
        if self._terminal_platform != TerminalPlatform.WINDOWS:
            config = self._mt5_config['rpyc']
            self._log.info(f"Connecting to RPYC host: {config.host}, port: {config.port}")
            return MetaTrader5(host=config.host, port=config.port, keep_alive=config.keep_alive)
        self._log.info(f"Connecting to IPC Process with client id: {self._client_id}")
        return MetaTrader5()

    def _create_ea_client(self) -> EAClient:
        """Create an EA-based MetaTrader5 client."""
        config = self._mt5_config['ea']
        self._log.info(f"Connecting to EA config: {config} with client id: {self._client_id}")
        return EAClient(config)

    def _create_ea_ipc_client(self) -> Dict[str, Union[MetaTrader5, EAClient]]:
        """Create a client that supports both EA and IPC modes."""
        return {'mt5': self._create_ipc_client(), 'ea': self._create_ea_client()}

    async def _fetch_terminal_info(self) -> None:
        """Fetch terminal version information."""
        retries = 5
        while retries > 0:
            server_info = await asyncio.to_thread(self._mt5_client['mt5'].version)
            if isinstance(server_info, tuple) and server_info[0] > 0:
                self._terminal_info = {
                    "version": int(server_info[0]),
                    "build": int(server_info[1]),
                    "build_release_date": server_info[2],
                    "connection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                return
            self._log.warning(f"Failed to receive terminal info. Retries left: {retries-1}")
            retries -= 1
            await asyncio.sleep(1)
        raise ConnectionError("Max retries reached. Failed to fetch terminal info.")

    def process_connection_closed(self) -> None:
        """Handle terminal disconnection."""
        for future in self._requests.get_futures():
            if not future.done():
                future.set_exception(ConnectionError("Terminal disconnected."))
        if self._is_mt5_connected.is_set():
            self._log.debug("_is_mt5_connected unset by connectionClosed.", LogColor.BLUE)
            self._is_mt5_connected.clear()

    def set_conn_state(self, state: int) -> None:
        """Set the current connection state."""
        self._conn_state = state

    def get_conn_state(self) -> int:
        """Retrieve the current connection state."""
        return self._conn_state

    def _log_connection_info(self) -> None:
        """Log connection details."""
        self._log.info(
            f"Connected to MT5 Terminal (v{self._terminal_info['version']}, "
            f"{self._terminal_info['build']}, {self._terminal_info['build_release_date']}) at "
            f"{self._terminal_info['connection_time']} | Client ID: {self._client_id}."
        )

    def _handle_error(self, id: int, code: int, msg: str) -> None:
        """Handle and log errors."""
        self._log.error(f"Error {code}: {msg}")
        raise ValueError(id, code, msg)

    def _handle_connection_error(self) -> None:
        """Handle connection errors."""
        if self._mt5_client['mt5']:
            code, msg = self._mt5_client['mt5'].last_error()
            error_info = TERMINAL_CONNECT_FAIL if code != MetaTrader5.RES_E_INTERNAL_FAIL_INIT else ErrorInfo(code, f"Terminal init failed: {msg}")
            self._handle_error(NO_VALID_ID, error_info.code(), error_info.msg())

    def _clear_clients(self) -> None:
        """Clear client references."""
        self._mt5_client = {'mt5': None, 'ea': None}
