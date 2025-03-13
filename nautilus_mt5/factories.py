import asyncio
import os
from functools import lru_cache

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.live.factories import LiveDataClientFactory
from nautilus_trader.live.factories import LiveExecClientFactory
from nautilus_trader.model.identifiers import AccountId

from nautilus_mt5.client import MetaTrader5Client, TerminalConnectionMode
from nautilus_mt5.constants import MT5_VENUE
from nautilus_mt5.config import (
    DockerizedMT5TerminalConfig,
    MetaTrader5DataClientConfig,
    MetaTrader5ExecClientConfig,
    MetaTrader5InstrumentProviderConfig,
    RpycConnectionConfig,
    EAConnectionConfig,
)
from nautilus_mt5.data import MetaTrader5DataClient
from nautilus_mt5.execution import MetaTrader5ExecutionClient
from nautilus_mt5.providers import MetaTrader5InstrumentProvider
from nautilus_mt5.terminal import DockerizedMT5Terminal

TERMINAL = None
MT5_CLIENTS: dict[tuple, MetaTrader5Client] = {}

@lru_cache(1)
def get_cached_mt5_client(
    loop: asyncio.AbstractEventLoop,
    msgbus: MessageBus,
    cache: Cache,
    clock: LiveClock,
    connection_mode: TerminalConnectionMode = TerminalConnectionMode.IPC,
    rpyc_config: RpycConnectionConfig = RpycConnectionConfig(),
    ea_config: EAConnectionConfig = EAConnectionConfig(),
    client_id: int = 1,
) -> MetaTrader5Client:
    """
    Retrieve or create a cached MetaTrader5Client using the provided key.

    Should a keyed client already exist within the cache, the function will return this instance. It's important
    to note that the key comprises a combination of the mode, rpyc_config, ea_config, and client_id.

    Parameters
    ----------
    loop: asyncio.AbstractEventLoop
        The event loop for the client.
    msgbus: MessageBus
        The message bus for the client.
    cache: Cache
        The cache for the client.
    clock: LiveClock
        The clock for the client.
    connection_mode: TerminalConnectionMode
        The connection mode for the MT5 Terminal.
    rpyc_config: RpycConnectionConfig
        The RPyc connection configuration.
    ea_config: EAConnectionConfig
        The EA connection configuration.
    client_id: int
        The unique session identifier for the Terminal. A single host can support multiple connections;
        however, each must use a different client_id.

    Returns
    -------
    MetaTrader5Client

    """
    PyCondition.not_none(
        connection_mode,
        "Please provide the `mode` for the MT5 Terminal connection.",
    )

    client_key: tuple = (connection_mode, client_id)

    if client_key not in MT5_CLIENTS:
        client = MetaTrader5Client(
            loop=loop,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            connection_mode=connection_mode,
            mt5_config={
                "rpyc": rpyc_config,
                "ea": ea_config,
            },
            client_id=client_id,
        )
        client.start()
        MT5_CLIENTS[client_key] = client
    return MT5_CLIENTS[client_key]


def get_cached_mt5_client_with_dockerized_gateway(
    loop: asyncio.AbstractEventLoop,
    msgbus: MessageBus,
    cache: Cache,
    clock: LiveClock,
    connection_mode: TerminalConnectionMode = TerminalConnectionMode.IPC,
    rpyc_config: RpycConnectionConfig = RpycConnectionConfig(),
    ea_config: EAConnectionConfig = EAConnectionConfig(),
    client_id: int = 1,
    dockerized_gateway: DockerizedMT5TerminalConfig | None = None,
) -> MetaTrader5Client:
    """
    Retrieve or create a cached MetaTrader5Client using the provided key.

    Should a keyed client already exist within the cache, the function will return this instance. It's important
    to note that the key comprises a combination of the mode, rpyc_config, ea_config, and client_id.

    Parameters
    ----------
    loop: asyncio.AbstractEventLoop
        The event loop for the client.
    msgbus: MessageBus
        The message bus for the client.
    cache: Cache
        The cache for the client.
    clock: LiveClock
        The clock for the client.
    connection_mode: TerminalConnectionMode
        The connection mode for the MT5 Terminal.
    rpyc_config: RpycConnectionConfig
        The RPyc connection configuration.
    ea_config: EAConnectionConfig
        The EA connection configuration.
    client_id: int
        The unique session identifier for the Terminal. A single host can support multiple connections;
        however, each must use a different client_id.
    dockerized_gateway: DockerizedMT5TerminalConfig, optional
        The configuration for the dockerized gateway. If this is provided, Nautilus will oversee the docker
        environment, facilitating the operation of the MT5 Terminal within.

    Returns
    -------
    MetaTrader5Client

    """
    global TERMINAL
    if dockerized_gateway:
        # PyCondition.equal(mode, TerminalConnectionMode.IPC, "mode", "TerminalConnectionMode.IPC")
        if TERMINAL is None:
            TERMINAL = DockerizedMT5Terminal(dockerized_gateway)
            TERMINAL.safe_start(wait=dockerized_gateway.timeout)
            rpyc_config.port = TERMINAL.port
        else:
            rpyc_config.port = TERMINAL.port
    else:
        PyCondition.not_none(
            connection_mode,
            "Please provide the `mode` for the MT5 Terminal connection.",
        )

    client_key: tuple = (connection_mode, client_id)

    if client_key not in MT5_CLIENTS:
        client = MetaTrader5Client(
            loop=loop,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            connection_mode=connection_mode,
            mt5_config={
                "rpyc": rpyc_config,
                "ea": ea_config,
            },
            client_id=client_id,
        )
        client.start()
        MT5_CLIENTS[client_key] = client
    return MT5_CLIENTS[client_key]


@lru_cache(1)
def get_cached_mt5_instrument_provider(
    client: MetaTrader5Client,
    config: MetaTrader5InstrumentProviderConfig,
) -> MetaTrader5InstrumentProvider:
    """
    Cache and return a MetaTrader5InstrumentProvider.

    If a cached provider already exists, then that cached provider will be returned.

    Parameters
    ----------
    client : MetaTrader5Client
        The client for the instrument provider.
    config: MetaTrader5InstrumentProviderConfig
        The instrument provider config.

    Returns
    -------
    MetaTrader5InstrumentProvider

    """
    return MetaTrader5InstrumentProvider(client=client, config=config)


class MT5LiveDataClientFactory(LiveDataClientFactory):
    """
    Factory for creating MetaTrader5 live data clients.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: MetaTrader5DataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> MetaTrader5DataClient:
        """
        Create a new MetaTrader5 data client.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop for the client.
        name : str
            The custom client ID.
        config : MetaTrader5DataClientConfig
            The configuration for the client.
        msgbus : MessageBus
            The message bus for the client.
        cache : Cache
            The cache for the client.
        clock : LiveClock
            The clock for the client.

        Returns
        -------
        MetaTrader5DataClient

        """
        client = get_cached_mt5_client(
            loop=loop,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            mode=config.mode,
            rpyc_config=config.rpyc_config,
            ea_config=config.ea_config,
            client_id=config.client_id,
        )

        # Get instrument provider singleton
        provider = get_cached_mt5_instrument_provider(
            client=client,
            config=config.instrument_provider,
        )

        # Create client
        data_client = MetaTrader5DataClient(
            loop=loop,
            client=client,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=provider,
            client_id=config.client_id,
            config=config,
            name=name,
        )
        return data_client


class MT5LiveExecClientFactory(LiveExecClientFactory):
    """
    Factory for creating MetaTrader5 live execution clients.
    """

    @staticmethod
    def create(
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: MetaTrader5ExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> MetaTrader5ExecutionClient:
        """
        Create a new MetaTrader5 execution client.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop for the client.
        name : str
            The custom client ID.
        config : MetaTrader5ExecClientConfig
            The configuration for the client.
        msgbus : MessageBus
            The message bus for the client.
        cache : Cache
            The cache for the client.
        clock : LiveClock
            The clock for the client.

        Returns
        -------
        MetaTrader5ExecutionClient

        """
        client = get_cached_mt5_client(
            loop=loop,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            mode=config.mode,
            rpyc_config=config.rpyc_config,
            ea_config=config.ea_config,
            client_id=config.client_id,
        )

        # Get instrument provider singleton
        provider = get_cached_mt5_instrument_provider(
            client=client,
            config=config.instrument_provider,
        )

        # Set account ID
        mt5_account = config.account_id or os.environ.get("MT5_ACCOUNT_NUMBER")
        assert (
            mt5_account
        ), f"Must pass `{config.__class__.__name__}.account_id` or set `MT5_ACCOUNT_NUMBER` env var."

        account_id = AccountId(f"{name or MT5_VENUE.value}-{mt5_account}")

        # Create client
        exec_client = MetaTrader5ExecutionClient(
            loop=loop,
            client=client,
            account_id=account_id,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=provider,
            config=config,
            name=name,
        )
        return exec_client
