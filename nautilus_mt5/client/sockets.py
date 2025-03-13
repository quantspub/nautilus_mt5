import asyncio
import itertools
from typing import Dict, List, Optional, Callable, Union
import msgspec
from nautilus_trader.common.component import Logger
from nautilus_trader.core.nautilus_pyo3 import SocketClient, SocketConfig

HOST = "127.0.0.1"
REST_PORT = 15556
STREAM_PORT = 15557
CRLF = b"\r\n"
ENCODING = "utf-8"
UNIQUE_ID = itertools.count()

def make_message(command: str, sub_command: str, parameters: List[str]) -> str:
        """
        Constructs a message in the format FXXX^Y^<parameters>.

        :param command: The command identifier (e.g., "F123").
        :param sub_command: The sub-command or parameter (e.g., "Y").
        :param parameters: A list of additional parameters (e.g., ["param1", "param2"]).
        :return: A formatted message string.
        """
        try:
            # Join the parameters with the '^' delimiter
            params_str = '^'.join(parameters)
            
            # Construct the message in the required format
            message = f"{command}^{sub_command}^{params_str}"
            
            return message
        
        except Exception as e:
            # Handle any errors that occur during message construction
            return f"Error: {str(e)}"
    
def parse_response_message(message: str) -> Union[Dict[str, Union[str, List[str]]], Dict[str, str]]:
        """
        Parses response message in the format FXXX^Y^<parameters>.
        The <parameters> part contains the server's response data.
        Handles hidden '^' delimiters and ensures data is properly extracted.

        :param message: The response or message string to parse.
        :return: A dictionary containing the command, sub_command, and data.
        """
        try:
            # Split the response or message by the '^' delimiter
            parts = message.split('^')
            
            # Ensure the response or message has at least three parts
            if len(parts) < 3:
                raise ValueError("Invalid format. Expected at least three parts separated by '^'.")
            
            # Extract the command and sub-command
            command = parts[0]
            sub_command = parts[1]
            
            # Extract the data (all remaining parts)
            data = parts[2:]
            
            # Find the index of the last non-empty data element
            last_non_empty_index = len(data) - 1
            while last_non_empty_index >= 0 and data[last_non_empty_index] == '':
                last_non_empty_index -= 1
            
            # Slice the data list up to the last non-empty index
            data = data[:last_non_empty_index + 1]
            
            # Check for hidden '^' delimiters in data (empty strings in the middle)
            if '' in data:
                raise ValueError("Invalid format. Hidden '^' delimiters detected in data.")
            
            # Return the parsed components as a dictionary
            response = {
                'command': command,
                'sub_command': sub_command,
                'data': data
            }
            return response
        
        except Exception as e:
            # Handle any errors that occur during parsing
            return {
                'error': str(e)
            }
                
class MetaTrader5SocketClient:
    """
    Manages the connection to a MetaTrader 5 server for streaming communication using NautilusTrader's SocketClient.

    Attributes:
        host (str): The server host address.
        port (int): The port for streaming communication.
        crlf (bytes): The delimiter used for message separation.
        encoding (str): The encoding used for message communication.
        handler (Callable[[bytes], None]): The callback function for handling incoming messages.
        client (Optional[SocketClient]): The socket client instance.
        log (Logger): Logger instance for logging messages.
        unique_id (int): Unique identifier for the client instance.
    """
    host: str
    rest_port: int
    stream_port: int
    rest_client: Optional[SocketClient]
    stream_client: Optional[SocketClient]
    encoding: str
    message_handler: Optional[Callable[[str], None]]
    is_stream_running: bool
    debug: bool

    def __init__(
        self,
        message_handler: Callable[[str], None],
        host: str = HOST,
        rest_port: int = REST_PORT,
        stream_port: int = STREAM_PORT,
        crlf: bytes = CRLF,
        encoding: str = ENCODING,
    ) -> None:
        self.host = host
        self.rest_port = rest_port
        self.stream_port = stream_port
        self.crlf = crlf
        self.encoding = encoding
        self.handler = message_handler
        self.rest_client: Optional[SocketClient] = None
        self.stream_client: Optional[SocketClient] = None
        self.log = Logger(type(self).__name__)
        self.unique_id = next(UNIQUE_ID)
        self.is_stream_running = False
        self.debug = False

    async def _connect_rest_client(self) -> None:
        """
        Establishes a connection to the MetaTrader 5 REST server.
        """
        if self.rest_client is not None and self.rest_client.is_active():
            self.log.info("REST client already connected")
            return

        self.log.info("Connecting MetaTrader 5 REST socket client...")
        config = SocketConfig(
            url=f"{self.host}:{self.rest_port}",
            ssl=False,
            suffix=self.crlf,
            handler=self.handler,
        )
        self.rest_client = await SocketClient.connect(            
                                config=config,            
                                post_connection=self.post_rest_connection,
                                post_reconnection=self.post_rest_reconnection)
        self.log.info("Connected")
        
    async def _connect_stream_client(self) -> None:
        """
        Establishes a connection to the MetaTrader 5 stream server.
        """
        if self.stream_client is not None and self.stream_client.is_active():
            self.log.info("Stream client already connected")
            return

        self.log.info("Connecting MetaTrader 5 stream socket client...")
        config = SocketConfig(
            url=f"{self.host}:{self.stream_port}",
            ssl=False,
            suffix=self.crlf,
            handler=self.handler,
        )
        self.stream_client = await SocketClient.connect(
            config=config,            
            post_connection=self.post_stream_connection,
            post_reconnection=self.post_stream_reconnection)
        self.log.info("Connected")
        
    async def connect(self) -> None:
        """
        Establishes a connection to the MetaTrader 5 server.
        """
        self.log.info("Connecting MetaTrader 5 socket client...")
        await self._connect_rest_client()
        await self._connect_stream_client()

        await self.post_connection()
        self.log.info("Connected")

    async def reconnect(self) -> None:
        """
        Re-establishes the connection to the MetaTrader 5 server.
        """
        if self.rest_client is None or self.stream_client is None:
            self.log.warning("Cannot reconnect: not connected")
            return

        if not self.rest_client.is_active() and not self.stream_client.is_active():
            self.log.warning(f"Cannot reconnect: rest client in {self.rest_client.mode()} mode | stream client in {self.stream_client.mode()} mode")
            return

        self.log.info("Reconnecting...")
        await self.rest_client.reconnect()
        await self.stream_client.reconnect()
        await asyncio.sleep(0.1)
        self.log.info("Reconnected")

    async def disconnect(self) -> None:
        """
        Closes the connection to the MetaTrader 5 server.
        """
        if self.rest_client is None or self.stream_client is None:
            self.log.warning("Cannot disconnect: not connected")
            return

        self.log.info(f"Disconnecting from rest client in {self.rest_client.mode()} mode | stream client in {self.stream_client.mode()} mode...")
        await self.rest_client.close()
        await self.stream_client.close()
        self.is_stream_running = False
        self.log.info("Disconnected")

    def is_active(self) -> bool:
        """
        Checks whether the client connection is active.

        Returns:
            bool: True if active, False otherwise.
        """
        return (self.rest_client.is_active() if self.rest_client else False) or \
               (self.stream_client.is_active() if self.stream_client else False)

    def is_reconnecting(self) -> bool:
        """
        Checks whether the client is reconnecting.

        Returns:
            bool: True if reconnecting, False otherwise.
        """
        return (self.rest_client.is_reconnecting() if self.rest_client else False) or \
               (self.stream_client.is_reconnecting() if self.stream_client else False)

    def is_disconnecting(self) -> bool:
        """
        Checks whether the client is disconnecting.

        Returns:
            bool: True if disconnecting, False otherwise.
        """
        return (self.rest_client.is_disconnecting() if self.rest_client else False) or \
               (self.stream_client.is_disconnecting() if self.stream_client else False)

    def is_closed(self) -> bool:
        """
        Checks whether the client is closed.

        Returns:
            bool: True if closed, False otherwise.
        """
        return (self.rest_client.is_closed() if self.rest_client else True) and \
               (self.stream_client.is_closed() if self.stream_client else True)

    async def send(self, message: str) -> None:
        """
        Sends a message to the MetaTrader 5 server.

        Args:
            message (str): The message to send.
        """
        if self.rest_client is None:
            raise RuntimeError("Cannot send message: no REST client")
        
        if self.stream_client is None:
            raise RuntimeError("Cannot send message: no stream client")

        await self.rest_client.send(message.encode(self.encoding))
        
    async def send_message(self, message: str) -> str:
        """
        Sends a request command/message to the server and returns the decoded response.

        :param message: The message to send.
        :return: The server's response as a decoded string.
        """
        try:
            reader, writer = await asyncio.open_connection(self.host, self.rest_port)
            writer.write(message.encode(self.encoding))
            await writer.drain()
            response = await reader.read(1024)
            writer.close()
            await writer.wait_closed()
            if self.debug:
                print(f"Sent: {message}, Received: {response.decode(self.encoding)}")
            return response.decode(self.encoding)
        except Exception as e:
            if self.debug:
                print(f"Error: {e}")
            return f"Error: {e}"

    def _listen_stream(self) -> None:
        """ Internal method to listen for streaming data. """
        try:
            while self.is_stream_running and self.stream_client is not None:
                data = self.stream_client.recv(1024)
                if data:
                    decoded_data = data.decode(self.encoding)
                    if self.debug:
                        self.log.debug(f"Stream Update: {decoded_data}")
                    if self.message_handler:
                        self.message_handler(decoded_data)
        except Exception as e:
            print(f"Streaming error: {e}")

    async def post_rest_connection(self) -> None:
        """
        Actions to be performed after establishing a REST connection.
        """
        pass
    
    async def post_stream_connection(self) -> None:
        """
        Actions to be performed after establishing a stream connection.
        
        Default Connects to the streaming server and continuously listens for updates.
        """
        try:
            self.is_stream_running = True
            await asyncio.to_thread(self._listen_stream)
        except Exception as e:
            self.log.error(f"Streaming connection error: {e}")
        
    async def post_connection(self) -> None:
        """
        Actions to be performed after establishing a connection.
        """
        pass
    
    def post_rest_reconnection(self) -> None:
        """
        Actions to be performed after re-establishing a REST connection.
        """
        pass
    
    def post_stream_reconnection(self) -> None:
        """
        Actions to be performed after re-establishing a stream connection.
        """
        pass

    def post_reconnection(self) -> None:
        """
        Actions to be performed after re-establishing a connection.
        """
        pass

    def post_disconnection(self) -> None:
        """
        Actions to be performed after disconnecting.
        """
        pass

    def auth_message(self) -> dict:
        """
        Constructs an authentication message.

        Returns:
            dict: The authentication message.
        """
        return {
            "op": "authentication",
            "id": self.unique_id,
        }


class MetaTrader5OrderStreamClient(MetaTrader5SocketClient):
    """
    Provides an order stream client for MetaTrader5.
    """

    def __init__(
        self,
        message_handler: Callable[[bytes], None],
        partition_matched_by_strategy_ref: bool = True,
        include_overall_position: str | None = None,
        customer_strategy_refs: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            message_handler=message_handler,
            **kwargs,
        )
        self.order_filter = {
            "includeOverallPosition": include_overall_position,
            "customerStrategyRefs": customer_strategy_refs,
            "partitionMatchedByStrategyRef": partition_matched_by_strategy_ref,
        }

    def post_connection(self):
        self._loop.create_task(self._post_connection())

    def post_reconnection(self):
        self._loop.create_task(self._post_connection())

    async def _post_connection(self):
        retries = 5
        for i in range(retries):
            try:
                subscribe_msg = {
                    "op": "orderSubscription",
                    "id": self.unique_id,
                    "orderFilter": self.order_filter,
                    "initialClk": None,
                    "clk": None,
                }
                await self.send(msgspec.json.encode(self.auth_message()))
                await self.send(msgspec.json.encode(subscribe_msg))
                return
            except Exception as e:
                self._log.error(f"Failed to send auth message({e}), retrying {i + 1}/{retries}...")
                await asyncio.sleep(1.0)


class MetaTrader5MarketStreamClient(MetaTrader5SocketClient):
    """
    Provides a MetaTrader5 market stream client.
    """

    def __init__(
        self,
        message_handler: Callable,
        **kwargs,
    ):
        super().__init__(
            message_handler=message_handler,
            **kwargs,
        )

    # TODO - Add support for initial_clk/clk reconnection
    async def send_subscription_message(
        self,
        market_ids: list | None = None,
        betting_types: list | None = None,
        event_type_ids: list | None = None,
        event_ids: list | None = None,
        turn_in_play_enabled: bool | None = None,
        market_types: list | None = None,
        venues: list | None = None,
        country_codes: list | None = None,
        race_types: list | None = None,
        initial_clk: str | None = None,
        clk: str | None = None,
        conflate_ms: int | None = None,
        heartbeat_ms: int | None = None,
        segmentation_enabled: bool = True,
        subscribe_book_updates=True,
        subscribe_trade_updates=True,
        subscribe_market_definitions=True,
        subscribe_ticker=True,
        subscribe_bsp_updates=True,
        subscribe_bsp_projected=True,
    ) -> None:
        filters = (
            market_ids,
            betting_types,
            event_type_ids,
            event_ids,
            turn_in_play_enabled,
            market_types,
            venues,
            country_codes,
            race_types,
        )
        assert any(filters), "Must pass at least one filter"
        assert any(
            (subscribe_book_updates, subscribe_trade_updates),
        ), "Must subscribe to either book updates or trades"
        if market_ids is not None:
            # TODO - Log a warning about inefficiencies of specific market ids - Won't receive any updates for new
            #  markets that fit criteria like when using event type / market type etc
            # logging.warning()
            pass
        market_filter = {
            "marketIds": market_ids,
            "bettingTypes": betting_types,
            "eventTypeIds": event_type_ids,
            "eventIds": event_ids,
            "turnInPlayEnabled": turn_in_play_enabled,
            "marketTypes": market_types,
            "venues": venues,
            "countryCodes": country_codes,
            "raceTypes": race_types,
        }
        data_fields = []
        if subscribe_book_updates:
            data_fields.append("EX_ALL_OFFERS")
        if subscribe_trade_updates:
            data_fields.append("EX_TRADED")
        if subscribe_ticker:
            data_fields.extend(["EX_TRADED_VOL", "EX_LTP"])
        if subscribe_market_definitions:
            data_fields.append("EX_MARKET_DEF")
        if subscribe_bsp_updates:
            data_fields.append("SP_TRADED")
        if subscribe_bsp_projected:
            data_fields.append("SP_PROJECTED")

        message = {
            "op": "marketSubscription",
            "id": self.unique_id,
            "marketFilter": market_filter,
            "marketDataFilter": {"fields": data_fields},
            "initialClk": initial_clk,
            "clk": clk,
            "conflateMs": conflate_ms,
            "heartbeatMs": heartbeat_ms,
            "segmentationEnabled": segmentation_enabled,
        }
        await self.send(msgspec.json.encode(message))

    def post_connection(self) -> None:
        self._loop.create_task(self._post_connection())

    def post_reconnection(self) -> None:
        super().post_reconnection()
        self._loop.create_task(self._post_connection())

    async def _post_connection(self) -> None:
        retries = 5
        for i in range(retries):
            try:
                await self.send(msgspec.json.encode(self.auth_message()))
                return
            except Exception as e:
                self._log.error(f"Failed to send auth message({e}), retrying {i + 1}/{retries}...")
                await asyncio.sleep(1.0)
