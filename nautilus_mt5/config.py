from __future__ import annotations
from typing import Optional
from nautilus_trader.common.config import NonNegativeInt
from nautilus_trader.config import InstrumentProviderConfig, LiveDataClientConfig, LiveExecClientConfig, NautilusConfig
from nautilus_mt5.data_types import MarketDataSubscription, TerminalConnectionMode, MT5Symbol
from nautilus_mt5.metatrader5 import EAConnectionConfig, RpycConnectionConfig


class DockerizedMT5TerminalConfig(NautilusConfig, frozen=True):
    """
    Configuration for Dockerized MT5 Terminal setup.

    Attributes:
        account_number (str | None): The Metatrader 5 account number. If None, will source the `MT5_ACCOUNT_NUMBER` environment variable.
        password (str | None): The Metatrader 5 account password. If None, will source the `MT5_PASSWORD` environment variable.
        server (str | None): The Metatrader 5 server name as it is specified in the terminal. If None, will source the `MT5_SERVER` environment variable.
        timeout (int): The timeout for trying to launch MT5 docker container when start=True. Default is 300.
    """
    account_number: str | None = None
    password: str | None = None
    server: str | None = None
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
    Configuration for MetaTrader5 Instrument Provider.

    Attributes:
        strict_symbology (bool): Whether to enforce strict symbology. Default is False.
        load_symbols (frozenset[MT5Symbol] | None): A frozenset of MT5Symbol objects that are loaded during the initial startup.
        cache_validity_days (int | None): The number of days for which the cache is valid. Default is None.
        pickle_path (str | None): Path to store the ContractDetails as pickle. Default is None.
    """
    strict_symbology: bool = False
    load_symbols: frozenset[MT5Symbol] | None = None
    cache_validity_days: int | None = None
    pickle_path: str | None = None

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


class MetaTrader5DataClientConfig(LiveDataClientConfig, frozen=True):
    """
    Configuration for MetaTrader5 Data Client.

    Attributes:
        client_id (int): The client ID. Default is 1.
        use_regular_trading_hours (bool): Whether to request data for Regular Trading Hours only. Default is True.
        market_data_subscription (MarketDataSubscription): The market data subscription type. Default is REALTIME.
        ignore_quote_tick_size_updates (bool): Whether to ignore quote tick size updates. Default is False.
        mode (TerminalConnectionMode): The connection mode. Default is TerminalConnectionMode.IPC.
        dockerized_gateway (DockerizedMT5TerminalConfig | None): The client's terminal container configuration. Default is None.
        ea_connection (Optional[EAConnectionConfig]): Configuration for EAClient. Default is None.
        rpyc_connection (Optional[RpycConnectionConfig]): Configuration for RPYC. Default is None.
        instrument_provider (MetaTrader5InstrumentProviderConfig): Configuration for instrument provider.
    """
    client_id: int = 1
    use_regular_trading_hours: bool = True
    market_data_subscription: MarketDataSubscription = MarketDataSubscription.REALTIME
    ignore_quote_tick_size_updates: bool = False
    mode: TerminalConnectionMode = TerminalConnectionMode.IPC
    dockerized_gateway: DockerizedMT5TerminalConfig | None = None
    ea_connection: Optional[EAConnectionConfig] = None
    rpyc_connection: Optional[RpycConnectionConfig] = None
    instrument_provider: MetaTrader5InstrumentProviderConfig = (
        MetaTrader5InstrumentProviderConfig()
    )


class MetaTrader5ExecClientConfig(LiveExecClientConfig, frozen=True):
    """
    Configuration for MetaTrader5 Execution Client.

    Attributes:
        client_id (int): The client ID. Default is 1.
        account_id (str | None): The account ID for MetaTrader 5 instance. Default is None.
        mode (TerminalConnectionMode): The connection mode. Default is TerminalConnectionMode.IPC.
        dockerized_gateway (DockerizedMT5TerminalConfig | None): The client's terminal container configuration. Default is None.
        ea_connection (Optional[EAConnectionConfig]): Configuration for EAClient. Default is None.
        rpyc_connection (Optional[RpycConnectionConfig]): Configuration for RPYC. Default is None.
        request_account_state_secs (NonNegativeInt): The request interval (seconds) for account state checks. Default is 300.
        instrument_provider (MetaTrader5InstrumentProviderConfig): Configuration for instrument provider.
    """
    client_id: int = 1
    account_id: str | None = None
    mode: TerminalConnectionMode = TerminalConnectionMode.IPC
    dockerized_gateway: DockerizedMT5TerminalConfig | None = None
    ea_connection: Optional[EAConnectionConfig] = None
    rpyc_connection: Optional[RpycConnectionConfig] = None
    request_account_state_secs: NonNegativeInt = 300
    instrument_provider: MetaTrader5InstrumentProviderConfig = (
        MetaTrader5InstrumentProviderConfig()
    )
