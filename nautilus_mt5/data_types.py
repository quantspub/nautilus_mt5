from enum import Enum
from typing import Literal, Optional, NamedTuple
import asyncio
from collections.abc import Callable
from decimal import Decimal
from enum import Enum

from nautilus_mt5.metatrader5 import MetaTrader5, RpycConnectionConfig, EAConnectionConfig
from nautilus_mt5.common import Requests, Subscriptions
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import Logger
from nautilus_trader.common.component import MessageBus
from nautilus_trader.config import NautilusConfig


class SubscriptionStatus(Enum):
    """
    Represents a MetaTrader subscription status.
    """

    UNSUBSCRIBED = 0
    PENDING_STARTUP = 1
    RUNNING = 2
    SUBSCRIBED = 3

class MarketDataSubscription(Enum):
    """
    Represents a MetaTrader market data subscription.
    """

    DELAYED = 0
    REALTIME = 1

class TerminalConnectionState(Enum):
    """
    Represents a MetaTrader terminal connection state.
    """

    DISCONNECTED = 0
    CONNECTED = 1
    AUTHENTICATED = 2
    
class TerminalConnectionMode(Enum):
    """Terminal Connection Mode type.
    
    Includes 3 client modes: IPC, EA, and EA_IPC.

    IPC: Mode for MetaTrader IPC communication on Windows.
    EA: Mode for EA communication using sockets.
    EA_IPC: Mode for combining EA and IPC communication (EA for streaming and IPC for request-reply).
    
    Since RPYC is used for IPC communication in Linux, it will be used for IPC mode in Linux (MetaTrader RPYC communication on Linux).
    """
    IPC = "IPC"
    EA = "EA"
    EA_IPC = "EA_IPC"

    def to_str(self) -> str:
        """Returns the string representation of the enum value."""
        return self.value
    
class TerminalPlatformType(Enum):
    """Terminal Platform type.
    
    Includes 2 platform types: WINDOWS and LINUX.
    """
    WINDOWS = "Windows"
    LINUX = "Linux"

    def to_str(self) -> str:
        """Returns the string representation of the enum value."""
        return self.value

class MT5Symbol(NautilusConfig, frozen=True, repr_omit_defaults=True):
    """
    Class describing an instrument's definition.

    Parameters
    ----------
    symbol: str
        Unique Symbol registered in Exchange.

    """
    sec_type: Literal[
        "CFD"
        "",
    ] = ""
    sym_id: int = 0
    symbol: str = ""
    broker: str = ""


class MT5SymbolDetails(NautilusConfig, frozen=True, repr_omit_defaults=True):
    """
    MT5SymbolDetails class to be used internally in Nautilus for ease of
    encoding/decoding.
    """

    under_sec_type: Optional[str] = None
    symbol: MT5Symbol | None = None
    custom: bool = False
    chart_mode: int = 0
    select: bool = True
    visible: bool = True
    session_deals: int = 0
    session_buy_orders: int = 0
    session_sell_orders: int = 0
    volume: float = 0.0
    volumehigh: float = 0.0
    volumelow: float = 0.0
    time: int = 0
    digits: int = 0
    spread: int = 0
    spread_float: bool = True
    ticks_bookdepth: int = 0
    trade_calc_mode: int = 0
    trade_mode: int = 0
    start_time: int = 0
    expiration_time: int = 0
    trade_stops_level: int = 0
    trade_freeze_level: int = 0
    trade_exemode: int = 1
    swap_mode: int = 1
    swap_rollover3days: int = 0
    margin_hedged_use_leg: bool = False
    expiration_mode: int = 7
    filling_mode: int = 1
    order_mode: int = 127
    order_gtc_mode: int = 0
    option_mode: int = 0
    option_right: int = 0
    bid: float = 0.0
    bidhigh: float = 0.0
    bidlow: float = 0.0
    ask: float = 0.0
    askhigh: float = 0.0
    asklow: float = 0.0
    last: float = 0.0
    lasthigh: float = 0.0
    lastlow: float = 0.0
    volume_real: float = 0.0
    volumehigh_real: float = 0.0
    volumelow_real: float = 0.0
    option_strike: float = 0.0
    point: float = 0.0
    trade_tick_value: float = 0.0
    trade_tick_value_profit: float = 0.0
    trade_tick_value_loss: float = 0.0
    trade_tick_size: float = 0.0
    trade_contract_size: float = 0.0
    trade_accrued_interest: float = 0.0
    trade_face_value: float = 0.0
    trade_liquidity_rate: float = 0.0
    volume_min: float = 0.0
    volume_max: float = 0.0
    volume_step: float = 0.0
    volume_limit: float = 0.0
    swap_long: float = 0.0
    swap_short: float = 0.0
    margin_initial: float = 0.0
    margin_maintenance: float = 0.0
    session_volume: float = 0.0
    session_turnover: float = 0.0
    session_interest: float = 0.0
    session_buy_orders_volume: float = 0.0
    session_sell_orders_volume: float = 0.0
    session_open: float = 0.0
    session_close: float = 0.0
    session_aw: float = 0.0
    session_price_settlement: float = 0.0
    session_price_limit_min: float = 0.0
    session_price_limit_max: float = 0.0
    margin_hedged: float = 0.0
    price_change: float = 0.0
    price_volatility: float = 0.0
    price_theoretical: float = 0.0
    price_greeks_delta: float = 0.0
    price_greeks_theta: float = 0.0
    price_greeks_gamma: float = 0.0
    price_greeks_vega: float = 0.0
    price_greeks_rho: float = 0.0
    price_greeks_omega: float = 0.0
    price_sensitivity: float = 0.0
    basis: Optional[str] = None
    currency_base: str = ''
    currency_profit: str = ''
    currency_margin: str = ''
    bank: Optional[str] = None
    description: str = ''
    exchange: Optional[str] = None
    formula: Optional[str] = None
    isin: Optional[str] = None
    name: str = ''
    page: Optional[str] = None
    path: Optional[str] = None


class AccountOrderRef(NamedTuple):
    account_id: str  # Account ID/Login Number of the account
    order_id: str


class MT5Position(NamedTuple):
    account_id: str  # Account ID/Login Number of the account
    symbol: MT5Symbol
    quantity: Decimal
    avg_cost: float
    commission: float

class BarData(NamedTuple):
    """
    Represents a bar of data for a symbol.
    """
    symbol: str
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: int
    complete: bool

class CommissionReport(NamedTuple):
    """
    Represents a commission report.
    """
    exec_id: str
    commission: float
    currency: str

class Execution(NamedTuple):
    """
    Represents an execution.
    """
    exec_id: str
    order_id: int
    time: int
    price: float
    quantity: float
    side: Literal["BUY", "SELL"]
    commission_report: CommissionReport


class BaseMixin:
    """
    Provide type hints for MetaTrader5Client Mixins.
    """

    # Client
    is_running: bool
    _loop: asyncio.AbstractEventLoop
    _log: Logger
    _cache: Cache
    _clock: LiveClock
    _msgbus: MessageBus
    _mode: TerminalConnectionMode
    _platform: TerminalPlatformType
    _rpyc_config: RpycConnectionConfig
    _ea_config: EAConnectionConfig
    _client_id: int
    _requests: Requests
    _subscriptions: Subscriptions
    _event_subscriptions: dict[str, Callable]
    _mt5_client: MetaTrader5
    _is_mt5_connected: asyncio.Event
    _start: Callable
    _startup: Callable
    _reset: Callable
    _stop: Callable
    _resume: Callable
    _degrade: Callable
    _end_request: Callable
    _await_request: Callable
    _next_req_id: Callable
    _resubscribe_all: Callable
    _create_task: Callable

    # Account
    accounts: Callable

    # Connection
    _reconnect_attempts: int
    _reconnect_delay: int
    _max_reconnect_attempts: int
    _indefinite_reconnect: bool

    # MarketData
    _bar_type_to_last_bar: dict[str, BarData | None]
    _order_id_to_order_ref: dict[int, AccountOrderRef]

    # Order
    _next_valid_order_id: int
    _exec_id_details: dict[
        str,
        dict[str, Execution | (CommissionReport | str)],
    ]
