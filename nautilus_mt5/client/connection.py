import asyncio
import functools
import platform
from typing import Dict, Union
from nautilus_trader.common.enums import LogColor

from nautilus_mt5.metatrader5 import MetaTrader5, EAClient
from nautilus_mt5.common import BaseMixin
from nautilus_mt5.client.types import TerminalConnectionMode, TerminalConnectionState, TerminalPlatform


class MetaTrader5ClientConnectionMixin(BaseMixin):
    """
    Manages the connection to Terminal for the MetaTrader5Client.

    This class is responsible for establishing and maintaining the terminal connection,
    handling server communication, monitoring the connection's health, and managing
    re-connections. When a connection is established and the client finishes initializing,
    the `_is_mt5_connected` event is set, and if the connection is lost, the
    `_is_mt5_connected` event is cleared.

    """

    async def _connect(self) -> None:
        """
        Establish the connection with Terminal.

        This initializes the connection, connects the terminal, fetches version
        information, and then sets a flag that the connection has been successfully
        established.

        """
        try:
            await self._initialize_and_connect()
            self._mt5_client['mt5'].set_conn_state(TerminalConnectionState.CONNECTING)
            await self._fetch_terminal_info()
            self._mt5_client['mt5'].set_conn_state(TerminalConnectionState.CONNECTED)
            self._log.info(
                f"Connected to MetaTrader 5 Terminal (v{self._terminal_version}, {self._build}, {self._build_release_date}) "
                f"at {self._mt5_client.connection_time} from {self._mt5_config.stream_host}:{self._mt5_config.stream_ws_port} | {self._mt5_config.stream_host}:{self._mt5_config.stream_callback_port}  "
                f"with client id: {self._client_id}."
            )
        except asyncio.CancelledError:
            self._log.info("Connection cancelled.")
            await self._disconnect()
        except Exception as e:
            self._log.error(f"Connection failed: {e}")
            if self._mt5_client['mt5']:
                self._mt5_client['mt5'].error(
                    NO_VALID_ID, CONNECT_FAIL.code(), CONNECT_FAIL.msg()
                )
            await self._handle_reconnect()

    async def _disconnect(self) -> None:
        """
        Disconnect from Terminal and clear the `_is_mt5_connected` flag.
        """
        try:
            # shut down connection to the MetaTrader 5 terminal
            self._mt5_client['mt5'].disconnect()
            if self._is_mt5_connected.is_set():
                self._log.debug(
                    "`_is_mt5_connected` unset by `_disconnect`.", LogColor.BLUE
                )
                self._is_mt5_connected.clear()
            self._log.info("Disconnected from MetaTrader 5 Terminal.")
        except Exception as e:
            self._log.error(f"Disconnection failed: {e}")

    async def _handle_reconnect(self) -> None:
        """
        Attempt to reconnect to Terminal.
        """
        self._reset()
        self._resume()

    async def _initialize_and_connect(self) -> None:
        """
        Initialize the connection parameters and connect the socket to Terminal.

        Sets up the host, port, and client ID for the EClient instance and increments
        the connection attempt counter. Logs the attempt information and connects the socket.
        """
        self._terminal_platform = TerminalPlatform(platform.system().capitalize())
        self._mt5_client = self._create_mt5_client()
        self._mt5_client['mt5'].id = self._client_id
        if 'ea' in self._mt5_client:
            self._mt5_client['ea'].id = self._client_id

        self._log.info(
            f"Connecting to {self._mt5_config.stream_host}:{self._mt5_config.stream_ws_port} | {self._mt5_config.stream_host}:{self._mt5_config.stream_callback_port} with client id: {self._client_id}",
        )
        await asyncio.to_thread(self._mt5_client['mt5'].connect)

    def _create_mt5_client(self) -> Dict[str, Union[MetaTrader5, EAClient]]:
        """
        Create and return the appropriate MetaTrader5 client based on the connection mode.
        """
        if self._terminal_connection_mode == TerminalConnectionMode.IPC:
            return self._create_ipc_client()
        elif self._terminal_connection_mode == TerminalConnectionMode.EA:
            return self._create_ea_client()
        elif self._terminal_connection_mode == TerminalConnectionMode.EA_IPC:
            return self._create_ea_ipc_client()
        else:
            raise ValueError(f"Invalid connection mode: {self._terminal_connection_mode}")

    def _create_ipc_client(self):
        """
        Create and return a MetaTrader5 client for IPC mode.
        """
        if self._terminal_platform != TerminalPlatform.WINDOWS:
            client = MetaTrader5(host=self._mt5_config['rpyc'].host, 
                               port=self._mt5_config['rpyc'].port,
                               keep_alive=self._mt5_config['rpyc'].keep_alive)
        else:
            client = MetaTrader5()
        
        return {'mt5': client, 'ea': None}

    def _create_ea_client(self):
        """
        Create and return a MetaTrader5 client for EA mode.
        """
        client = EAClient(self._ea_config)
        return {'mt5': None, 'ea': client}

    def _create_ea_ipc_client(self):
        """
        Create and return a MetaTrader5 client for EA_IPC mode.
        """
        mt5_client = MetaTrader5(host=self._mt5_config['rpyc'].host, 
                                 port=self._mt5_config['rpyc'].port,
                                 keep_alive=self._mt5_config['rpyc'].keep_alive) if self._terminal_platform != TerminalPlatform.WINDOWS else MetaTrader5()
        ea_client = EAClient(self._ea_config)
        return {'mt5': mt5_client, 'ea': ea_client}

    async def _fetch_terminal_info(self) -> None:
        """
        Receive and process the terminal version information.

        Waits for the terminal to send its version information.
        Retries receiving this information up to a specified number of attempts.

        Raises
        ------
        ConnectionError
            If the server version information is not received within the allotted retries.

        """
        retries_remaining = 5

        while retries_remaining > 0:
            server_info = await asyncio.to_thread(self._mt5_client['mt5'].version)
            if isinstance(server_info, tuple) and server_info[0] > 0:
                self._process_terminal_version(server_info)
                break
            else:
                self._log.debug(f"Received empty response. {server_info}")

            retries_remaining -= 1
            self._log.warning(
                "Failed to receive server version information. "
                f"Retries remaining: {retries_remaining}.",
            )
            await asyncio.sleep(1)

        if retries_remaining == 0:
            raise ConnectionError(
                "Max retry attempts reached. Failed to receive server version information.",
            )

    def _process_terminal_version(self, fields: tuple[str]) -> None:
        """
        Process and log the terminal version information.
        """
        terminal_version, build, build_release_date = (
            int(fields[0]),
            int(fields[1]),
            fields[2],
        )
        self._terminal_version = terminal_version
        self._build = build
        self._build_release_date = build_release_date

    def process_connection_closed(self) -> None:
        """
        Indicate the connection has closed.

        Following a API <-> Terminal broken socket connection, this function is not called
        automatically but must be triggered by API client code.

        """
        for future in self._requests.get_futures():
            if not future.done():
                future.set_exception(ConnectionError("Terminal disconnected."))
        if self._is_mt5_connected.is_set():
            self._log.debug(
                "`_is_mt5_connected` unset by `connectionClosed`.", LogColor.BLUE
            )
            self._is_mt5_connected.clear()
