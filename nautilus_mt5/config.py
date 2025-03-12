from __future__ import annotations
from typing import Callable, Literal, Optional
from nautilus_trader.common.config import NonNegativeInt
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.config import NautilusConfig

from nautilus_mt5.config import MarketDataSubscription  
# from nautilus_mt5.common import (
#     MarketDataType as MT5MarketDataType,
#     TerminalConnectionMode,
# )
# from nautilus_mt5.common import MT5Symbol

class RpycConfig(NautilusConfig, frozen=True):
    """
    Configuration for RPYC.

    Parameters:
        host (str): Host address for the RPYC connection. Default is "localhost".
        port (int): Port number for the RPYC connection. Default is 18812.
        keep_alive (bool): Whether to keep the RPYC connection alive. Default is False.
    """
    host: str = "localhost"
    port: int = 18812
    keep_alive: bool = False


class EAClientConfig(NautilusConfig, frozen=True):
    """
    Configuration for EAClient.

    Parameters:
        host (str): Host address for the EAClient. Default is "127.0.0.1".
        rest_port (int): Port number for REST API. Default is 15556.
        stream_port (int): Port number for streaming data. Default is 15557.
        encoding (str): Encoding type. Default is 'utf-8'.
        use_socket (bool): Whether to use sockets for communication. Default is True.
        enable_stream (bool): Flag to enable or disable streaming. Default is True.
        callback (Optional[Callable]): Callback function to handle streamed data. Default is None.
        debug (bool): Whether to enable debug messages. Default is False.
    """
    host: str = "127.0.0.1"
    rest_port: int = 15556
    stream_port: int = 15557
    encoding: str = 'utf-8'
    use_socket: bool = True
    enable_stream: bool = True
    callback: Optional[Callable] = None
    debug: bool = False


class DockerizedMT5TerminalConfig(NautilusConfig, frozen=True):
    """
    Configuration for `DockerizedMT5Terminal` setup when working with containerized
    installations.

    Parameters
    ----------
    account_number : str, optional
        The Metatrader 5 account number.
        If ``None`` then will source the `MT5_ACCOUNT_NUMBER` environment variable.
    password : str, optional
        The Metatrader 5 account password.
        If ``None`` then will source the `MT5_PASSWORD` environment variable.
    server : str, optional
        The Metatrader 5 server name as it is specified in the terminal.
        If ``None`` then will source the `MT5_SERVER` environment variable.
    read_only_api: bool, optional, default True
        If True, no order execution is allowed. Set read_only_api=False to allow executing live orders.
    timeout: int, optional
        The timeout for trying to launch MT5 docker container when start=True

    """

    account_number: str | None = None
    password: str | None = None
    server: str | None = None
    trading_mode: Literal["paper", "live"] = "paper"
    read_only_api: bool = True
    timeout: int = 300

    def __repr__(self):
        masked_account_number = self._mask_sensitive_info(self.account_number)
        masked_password = self._mask_sensitive_info(self.password)
        return (
            f"DockerizedMT5TerminalConfig(account_number={masked_account_number}, "
            f"password={masked_password}, server={self.server}, "
            f"read_only_api={self.read_only_api}, timeout={self.timeout})"
        )

    @staticmethod
    def _mask_sensitive_info(value: str | None) -> str:
        if value is None:
            return "None"
        return (
            value[0] + "*" * (len(value) - 2) + value[-1]
            if len(value) > 2
            else "*" * len(value)
        )


class MetaTrader5InstrumentProviderConfig(InstrumentProviderConfig, frozen=True):
    """
    Configuration for instances of `MetaTrader5InstrumentProvider`.

    Specify either `load_ids`, `load_symbols`, or both to dictate which instruments the system loads upon start.
    It should be noted that the `MetaTrader5InstrumentProviderConfig` isn't limited to the instruments
    initially loaded. Instruments can be dynamically requested and loaded at runtime as needed.

    Parameters
    ----------
    load_all : bool, default False
        Note: Loading all instruments isn't supported by the MetaTrader5InstrumentProvider.
        As such, this parameter is not applicable.
    load_ids : FrozenSet[InstrumentId], optional
        A frozenset of `InstrumentId` instances that should be loaded during startup. These represent the specific
        instruments that the provider should initially load.
    load_symbols: FrozenSet[MT5Symbol], optional
        A frozenset of `MT5Symbol` objects that are loaded during the initial startup. These specific symbols
        correspond to the instruments that the provider preloads. It's important to note that while the `load_ids`
        option can be used for loading individual instruments, using `load_symbols` allows for a more versatile
        loading of several related instruments like Futures and Options that share the same underlying asset.
    cache_validity_days: int (default: None)
        Default None, will request fresh pull upon starting of TradingNode [only once].
        Setting value will pull the instruments at specified interval, useful when TradingNode runs for many days.
        Example: value set to 1, InstrumentProvider will make fresh pull every day even if TradingNode is not restarted.
    pickle_path: str (default: None)
        If provided valid path, will store the ContractDetails as pickle, and use during cache_validity period.

    """

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MetaTrader5InstrumentProviderConfig):
            return False
        return (
            self.load_ids == other.load_ids and self.load_symbols == other.load_symbols
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.load_ids,
                self.load_symbols,
            ),
        )

    strict_symbology: bool = False
    load_symbols: frozenset[MT5Symbol] | None = None

    cache_validity_days: int | None = None
    pickle_path: str | None = None


class MetaTrader5DataClientConfig(LiveDataClientConfig, frozen=True):
    """
    Configuration for ``MetaTrader5DataClient`` instances.

    Parameters
    ----------
    mt5_host : str, default "127.0.0.1"
        The hostname or ip address for the MetaTrader Terminal (MT5).
    mt5_port : int, default None
        The port for the gateway server. ("web"/"rpyc" defaults: 8000/18812)
    mt5_client_id: int, default 1
        The client_id to be passed into connect call.
    use_regular_trading_hours : bool
        If True, will request data for Regular Trading Hours only.
        Only applies to bar data - will have no effect on trade or tick data feeds.
    market_data_type : MT5MarketDataType, default REALTIME
        Set which MT5MarketDataType to be used by MetaTrader5Client.
        Configure `MT5MarketDataType.DELAYED` to use with account without data subscription.
    ignore_quote_tick_size_updates : bool
        If set to True, the QuoteTick subscription will exclude ticks where only the size has changed but not the price.
        This can help reduce the volume of tick data. When set to False (the default), QuoteTick updates will include
        all updates, including those where only the size has changed.
    dockerized_gateway : DockerizedMT5TerminalConfig, Optional
        The client's terminal container configuration.
    id (int): ID of the client. Default is 1.
    mode (Mode): Mode of the client. Default is Mode.IPC.
    ea_client (Optional[EAClientConfig]): Configuration for EAClient. Default is None.
    rpyc (Optional[RpycConfig]): Configuration for RPYC. Default is None.
    debug (bool): Whether to enable debug messages. Default is False.
    """

    instrument_provider: MetaTrader5InstrumentProviderConfig = (
        MetaTrader5InstrumentProviderConfig()
    )

    mt5_host: str = "127.0.0.1"
    mt5_port: int | None = None
    mt5_client_id: int = 1
    use_regular_trading_hours: bool = True
    market_data_type: MarketDataSubscription = MarketDataSubscription.REALTIME
    ignore_quote_tick_size_updates: bool = False
    dockerized_gateway: DockerizedMT5TerminalConfig | None = None
    id: int = 1
    mode: TerminalConnectionMode = TerminalConnectionMode.IPC
    ea_client: Optional[EAClientConfig] = None
    rpyc: Optional[RpycConfig] = None
    debug: bool = False

class MetaTrader5ExecClientConfig(LiveExecClientConfig, frozen=True):
    """
    Configuration for ``MetaTrader5ExecClient`` instances.

    Parameters
    ----------
    mt5_host : str, default "127.0.0.1"
        The hostname or ip address for the MetaTrader Terminal (MT5).
    mt5_port : int, default None
        The port for the gateway server. ("web"/"rpyc" defaults: 8000/18812)
    mt5_client_id: int, default 1
        The client_id to be passed into connect call.
    account_id : str
        Represents the account_id for MetaTrader 5 instance to which the Terminal is logged in.
        It's crucial that the account_id aligns with the account for which the Terminal is logged in.
        If the account_id is `None`, the system will fallback to use the `MT5_ACCOUNT_NUMBER` from environment variable.
    dockerized_gateway : DockerizedMT5TerminalConfig, Optional
        The client's terminal container configuration.
    id (int): ID of the client. Default is 1.
    mode (Mode): Mode of the client. Default is Mode.IPC.
    ea_client (Optional[EAClientConfig]): Configuration for EAClient. Default is None.
    rpyc (Optional[RpycConfig]): Configuration for RPYC. Default is None.
    request_account_state_secs : NonNegativeInt, default 300 (5 minutes)
        The request interval (seconds) for account state checks.
        If zero, then will not request account state from MetaTrader.
    """

    client_id: int = 1
    account_id: str | None = None
    dockerized_gateway: DockerizedMT5TerminalConfig | None = None
    mode: TerminalConnectionMode = TerminalConnectionMode.IPC
    ea_client: Optional[EAClientConfig] = None
    rpyc: Optional[RpycConfig] = None
    request_account_state_secs: NonNegativeInt = 300
    instrument_provider: MetaTrader5InstrumentProviderConfig = (
        MetaTrader5InstrumentProviderConfig()
    )
