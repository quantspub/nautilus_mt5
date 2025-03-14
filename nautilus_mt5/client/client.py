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
from nautilus_mt5.client.symbol import MetaTrader5ClientSymbolMixin
from nautilus_mt5.client.market_data import MetaTrader5ClientMarketDataMixin
from nautilus_mt5.client.order import MetaTrader5ClientOrderMixin
from nautilus_mt5.constants import MT5_VENUE


class MetaTrader5Client(Component,
                        MetaTrader5ClientConnectionMixin,
                        MetaTrader5ClientAccountMixin,
                        MetaTrader5ClientSymbolMixin,
                        MetaTrader5ClientMarketDataMixin,
                        MetaTrader5ClientOrderMixin,):
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
        
        # Terminal API Decoder
        self.decoder: Decoder = Decoder(self)

        # Tasks
        self._connection_watchdog_task: asyncio.Task | None = None
        self._terminal_incoming_msg_reader_task: asyncio.Task | None = None
        self._internal_msg_queue_processor_task: asyncio.Task | None = None
        self._internal_msg_queue: asyncio.Queue = asyncio.Queue()
        self._msg_handler_processor_task: asyncio.Task | None = None
        self._msg_handler_task_queue: asyncio.Queue = asyncio.Queue()

        # Event flags
        self._is_client_ready: asyncio.Event = asyncio.Event()
        self._is_mt5_connected: asyncio.Event = asyncio.Event()

        # Hot caches
        self.registered_nautilus_clients: set = set()
        self._event_subscriptions: dict[str, Callable] = {}

        # Subscriptions
        self._requests = Requests()
        self._subscriptions = Subscriptions()

        # AccountMixin
        self._account_ids: set[str] = set()

        # ConnectionMixin
        self._connection_attempts: int = 0
        self._max_connection_attempts: int = int(
            os.getenv("MT5_MAX_CONNECTION_ATTEMPTS", 0)
        )
        self._indefinite_reconnect: bool = (
            False if self._max_connection_attempts else True
        )
        self._reconnect_delay: int = 5  # seconds

        # MarketDataMixin
        self._bar_type_to_last_bar: dict[str, BarData | None] = {}

        # OrderMixin
        self._exec_id_details: dict[
            str,
            dict[str, Execution | (CommissionReport | str)],
        ] = {}
        self._order_id_to_order_ref: dict[int, AccountOrderRef] = {}
        self._next_valid_order_id: int = -1

        # Start client
        self._request_id_seq: int = 10000

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
    
    async def _start_async(self):
        self._log.info(f"Starting MetaTrader5Client ({self._client_id})...")
        while not self._is_mt5_connected.is_set():
            try:
                self._connection_attempts += 1
                if (
                    not self._indefinite_reconnect
                    and self._connection_attempts > self._max_connection_attempts
                ):
                    self._log.error(
                        "Max connection attempts reached. Connection failed."
                    )
                    self._stop()
                    break
                if self._connection_attempts > 1:
                    self._log.info(
                        f"Attempt {self._connection_attempts}: Attempting to reconnect in {self._reconnect_delay} seconds...",
                    )
                    await asyncio.sleep(self._reconnect_delay)
                await self._connect()
                self._start_terminal_incoming_msg_reader()
                self._start_internal_msg_queue_processor()
                self._mt5Client.start_api()
                # Terminal will send process_managed_accounts a message upon successful connection,
                # which will set the `_is_mt5_connected` event. This typically takes a few
                # seconds, so we wait for it here.
                await asyncio.wait_for(self._is_mt5_connected.wait(), 15)
                self._start_connection_watchdog()
            except asyncio.TimeoutError:
                self._log.error("Client failed to initialize. Connection timeout.")
            except Exception as e:
                self._log.exception("Unhandled exception in client startup", e)
                self._stop()

        self._is_client_ready.set()
        self._log.debug("`_is_client_ready` set by `_start_async`.", LogColor.BLUE)
        self._connection_attempts = 0

    def _start_terminal_incoming_msg_reader(self) -> None:
        """
        Start the incoming message reader task.
        """
        if self._terminal_incoming_msg_reader_task:
            self._terminal_incoming_msg_reader_task.cancel()
        self._terminal_incoming_msg_reader_task = self._create_task(
            self._run_terminal_incoming_msg_reader(),
        )

    def _start_internal_msg_queue_processor(self) -> None:
        """
        Start the internal message queue processing task.
        """
        if self._internal_msg_queue_processor_task:
            self._internal_msg_queue_processor_task.cancel()
        self._internal_msg_queue_processor_task = self._create_task(
            self._run_internal_msg_queue_processor(),
        )
        if self._msg_handler_processor_task:
            self._msg_handler_processor_task.cancel()
        self._msg_handler_processor_task = self._create_task(
            self._run_msg_handler_processor(),
        )

    def _start_connection_watchdog(self) -> None:
        """
        Start the connection watchdog task.
        """
        if self._connection_watchdog_task:
            self._connection_watchdog_task.cancel()
        self._connection_watchdog_task = self._create_task(
            self._run_connection_watchdog(),
        )

    def _stop(self) -> None:
        """
        Stop the client and cancel running tasks.
        """
        self._create_task(self._stop_async())

    async def _stop_async(self) -> None:
        self._log.info(f"Stopping MetaTrader5Client ({self._client_id})...")

        if self._is_client_ready.is_set():
            self._is_client_ready.clear()
            self._log.debug("`_is_client_ready` unset by `_stop_async`.", LogColor.BLUE)

        # Cancel tasks
        tasks = [
            self._connection_watchdog_task,
            self._terminal_incoming_msg_reader_task,
            self._internal_msg_queue_processor_task,
            self._msg_handler_processor_task,
        ]
        for task in tasks:
            if task and not task.cancelled():
                task.cancel()

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
            self._log.info("All tasks canceled successfully.")
        except Exception as e:
            self._log.exception(f"Error occurred while canceling tasks: {e}", e)

        self._mt5Client.disconnect()
        self._account_ids = set()
        self.registered_nautilus_clients = set()

    def _reset(self) -> None:
        """
        Restart the client.
        """

        async def _reset_async():
            self._log.info(f"Resetting MetaTrader5Client ({self._client_id})...")
            await self._stop_async()
            await self._start_async()

        self._create_task(_reset_async())

    def _resume(self) -> None:
        """
        Resume the client and resubscribe to all subscriptions.
        """

        async def _resume_async():
            print(f"Resuming MetaTrader5Client ({self._client_id})...")
            print("self._is_client_ready => ", self._is_client_ready.is_set())
            await self._is_client_ready.wait()
            self._log.info(f"Resuming MetaTrader5Client ({self._client_id})...")
            await self._resubscribe_all()

        self._create_task(_resume_async())

    def _degrade(self) -> None:
        """
        Degrade the client when connectivity is lost.
        """
        if not self.is_degraded:
            self._log.info(f"Degrading MetaTrader5Client ({self._client_id})...")
            self._is_client_ready.clear()
            self._account_ids = set()

    async def _resubscribe_all(self) -> None:
        """
        Cancel and restart all subscriptions.
        """
        subscriptions = self._subscriptions.get_all()
        subscription_names = ", ".join(
            [str(subscription.name) for subscription in subscriptions]
        )
        self._log.info(
            f"Resubscribing to {len(subscriptions)} subscriptions: {subscription_names}"
        )

        for subscription in self._subscriptions.get_all():
            self._log.info(f"Resubscribing to {subscription.name} subscription...")
            try:
                if iscoroutinefunction(subscription.handle):
                    await subscription.handle()
                else:
                    await asyncio.to_thread(subscription.handle)
            except Exception as e:
                self._log.exception(f"Failed to resubscribe to {subscription}", e)

    async def wait_until_ready(self, timeout: int = 300) -> None:
        """
        Check if the client is running and ready within a given timeout.

        Parameters
        ----------
        timeout : int, default 300
            Time in seconds to wait for the client to be ready.

        """
        try:
            if not self._is_client_ready.is_set():
                await asyncio.wait_for(self._is_client_ready.wait(), timeout)
        except asyncio.TimeoutError as e:
            self._log.error(f"Client is not ready. {e}")

    async def _run_connection_watchdog(self) -> None:
        """
        Run a watchdog to monitor and manage the health of the terminal connection.

        Continuously checks the connection status, manages client state based on
        connection health, and handles subscription management in case of network
        failure or forced MT5 connection reset.

        """
        try:
            while True:
                await asyncio.sleep(1)
                if (
                    not self._is_mt5_connected.is_set()
                    or not self._mt5Client.is_connected()
                ):
                    self._log.error(
                        "Connection watchdog detects connection lost.",
                    )
                    await self._handle_disconnection()
        except asyncio.CancelledError:
            self._log.debug("Client connection watchdog task was canceled.")

    async def _handle_disconnection(self) -> None:
        """
        Handle the disconnection of the client from Terminal.
        """
        if self.is_running:
            self._degrade()

        if self._is_mt5_connected.is_set():
            self._log.debug(
                "`_is_mt5_connected` unset by `_handle_disconnection`.", LogColor.BLUE
            )
            self._is_mt5_connected.clear()

        await asyncio.sleep(5)
        await self._handle_reconnect()

    def _create_task(
        self,
        coro: Coroutine,
        log_msg: str | None = None,
        actions: Callable | None = None,
        success: str | None = None,
    ) -> asyncio.Task:
        """
        Create an asyncio task with error handling and optional callback actions.

        Parameters
        ----------
        coro : Coroutine
            The coroutine to run.
        log_msg : str, optional
            The log message for the task.
        actions : Callable, optional
            The actions callback to run when the coroutine is done.
        success : str, optional
            The log message to write on actions success.

        Returns
        -------
        asyncio.Task

        """
        log_msg = log_msg or coro.__name__
        self._log.debug(f"Creating task {log_msg}.")
        task = self._loop.create_task(
            coro,
            name=coro.__name__,
        )
        task.add_done_callback(
            functools.partial(
                self._on_task_completed,
                actions,
                success,
            ),
        )
        return task

    def _on_task_completed(
        self,
        actions: Callable | None,
        success: str | None,
        task: asyncio.Task,
    ) -> None:
        """
        Handle the completion of a task.

        Parameters
        ----------
        actions : Callable, optional
            Callback actions to execute upon task completion.
        success : str, optional
            Success log message to display on successful completion of actions.
        task : asyncio.Task
            The asyncio Task that has been completed.

        """
        if task.exception():
            self._log.error(
                f"Error on `{task.get_name()}`: {task.exception()!r}",
            )
        else:
            if actions:
                try:
                    actions()
                except Exception as e:
                    self._log.error(
                        f"Failed triggering action {actions.__name__} on `{task.get_name()}`: "
                        f"{e!r}",
                    )
            if success:
                self._log.info(success, LogColor.GREEN)

    def subscribe_event(self, name: str, handler: Callable) -> None:
        """
        Subscribe a handler function to a named event.

        Parameters
        ----------
        name : str
            The name of the event to subscribe to.
        handler : Callable
            The handler function to be called when the event occurs.

        """
        self._event_subscriptions[name] = handler

    def unsubscribe_event(self, name: str) -> None:
        """
        Unsubscribe a handler from a named event.

        Parameters
        ----------
        name : str
            The name of the event to unsubscribe from.

        """
        self._event_subscriptions.pop(name)

    async def _await_request(
        self,
        request: Request,
        timeout: int,
        default_value: Any | None = None,
    ) -> Any:
        """
        Await the completion of a request within a specified timeout.

        Parameters
        ----------
        request : Request
            The request object to await.
        timeout : int
            The maximum time to wait for the request to complete, in seconds.
        default_value : Any, optional
            The default value to return if the request times out or fails. Defaults to None.

        Returns
        -------
        Any
            The result of the request, or default_value if the request times out or fails.

        """

        try:
            return await asyncio.wait_for(request.future, timeout)
        except asyncio.TimeoutError as e:
            self._log.warning(f"Request timed out for {request}. Ending request.")
            self._end_request(request.req_id, success=False, exception=e)
            return default_value
        except ConnectionError as e:
            self._log.error(f"Connection error during {request}. Ending request.")
            self._end_request(request.req_id, success=False, exception=e)
            return default_value

    def _end_request(
        self,
        req_id: int,
        success: bool = True,
        exception: type | BaseException | None = None,
    ) -> None:
        """
        End a request with a specified result or exception.

        Parameters
        ----------
        req_id : int
            The request ID to conclude.
        success : bool, optional
            Whether the request was successful. Defaults to True.
        exception : type | BaseException | None, optional
            An exception to set on request failure. Defaults to None.

        """
        if not (request := self._requests.get(req_id=req_id)):
            return

        if not request.future.done():
            if success:
                request.future.set_result(request.result)
            else:
                request.cancel()
                if exception:
                    request.future.set_exception(exception)
        self._requests.remove(req_id=req_id)

    async def _run_terminal_incoming_msg_reader(self) -> None:
        """
        Continuously read messages from Terminal and then put them in the internal
        message queue for processing.

        """
        self._log.debug("Client Terminal incoming message reader started.")
        try:
            while self._mt5Client.is_connected():
                data = await asyncio.to_thread(self._mt5Client.recv_msg)
                # self._log.debug(f"Msg data received: {data!s}")
                # if data is None:
                #     self._log.debug("No data available, incoming packets are needed.")
                #     break

                # Place msg in the internal queue for processing
                self._loop.call_soon_threadsafe(
                    self._internal_msg_queue.put_nowait, data
                )
        except asyncio.CancelledError:
            self._log.debug("Client Terminal incoming message reader was cancelled.")
        except Exception as e:
            self._log.exception(
                "Unhandled exception in Client Terminal incoming message reader", e
            )
        finally:
            if self._is_mt5_connected.is_set() and not self.is_disposed:
                self._log.debug(
                    "`_is_mt5_connected` unset by `_run_terminal_incoming_msg_reader`.",
                    LogColor.BLUE,
                )
                self._is_mt5_connected.clear()
            self._log.debug("Client Terminal incoming message reader stopped.")

    async def _run_internal_msg_queue_processor(self) -> None:
        """
        Continuously process messages from the internal incoming message queue.
        """
        self._log.debug(
            "Client internal message queue processor started.",
        )
        try:
            while (
                self._mt5Client.is_connected() or not self._internal_msg_queue.empty()
            ):
                msg = await self._internal_msg_queue.get()
                if not await self._process_message(msg):
                    break
                self._internal_msg_queue.task_done()
        except asyncio.CancelledError:
            log_msg = f"Internal message queue processing was cancelled. (qsize={self._internal_msg_queue.qsize()})."
            (
                self._log.warning(log_msg)
                if not self._internal_msg_queue.empty()
                else self._log.debug(
                    log_msg,
                )
            )
        finally:
            self._log.debug("Internal message queue processor stopped.")

    async def _process_message(self, msg: Any) -> bool:
        """
        Process a single message from Terminal.

        Parameters
        ----------
        msg : Any
            The message to be processed.

        Returns
        -------
        bool

        """
        self._log.debug(f"Msg received: {msg}")

        asyncio.run_coroutine_threadsafe(self.decoder.decode(msg), self._loop)
        return True

    async def _run_msg_handler_processor(self):
        """
        Asynchronously processes handler tasks from the message handler task queue.

        Continuously retrieves and executes tasks from `msg_handler_task_queue`, which are
        typically partial functions representing message handling operations received from the mt5api wrapper.
        The method ensures each task is awaited, thereby executing it. After task execution, it marks
        the task as done in the queue.

        This method is designed to run indefinitely until externally cancelled, typically as part
        of an application shutdown or when the handling context changes requiring a halt in operations.

        """
        try:
            while True:
                handler_task = await self._msg_handler_task_queue.get()
                await handler_task()
                self._msg_handler_task_queue.task_done()
        except asyncio.CancelledError:
            log_msg = f"Handler task processing was cancelled. (qsize={self._msg_handler_task_queue.qsize()})."
            (
                self._log.warning(log_msg)
                if not self._internal_msg_queue.empty()
                else self._log.debug(
                    log_msg,
                )
            )
        finally:
            self._log.debug("Handler task processor stopped.")

    def submit_to_msg_handler_queue(self, task: Callable[..., Any]) -> None:
        """
        Submit a task to the message handler's queue for processing.

        This method places a callable task into the message handler task queue,
        ensuring it's scheduled for asynchronous execution according to the queue's
        order. The operation is non-blocking and immediately returns after queueing the task.

        Parameters
        ----------
        task : Callable[..., Any]
            The task to be queued. This task should be a callable that matches
            the expected signature for tasks processed by the message handler.

        """
        self._log.debug(f"Submitting task to message handler queue: {task}")
        asyncio.run_coroutine_threadsafe(
            self._msg_handler_task_queue.put(task), self._loop
        )

    def _next_req_id(self) -> int:
        """
        Generate the next sequential request ID.

        Returns
        -------
        int

        """
        new_id = self._request_id_seq
        self._request_id_seq += 1
        return new_id

