from typing import Literal, Optional, NamedTuple
from decimal import Decimal

from nautilus_trader.config import NautilusConfig


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
    side: Literal[
        "BUY", 
        "SELL", 
        "BUY_LIMIT", 
        "SELL_LIMIT", 
        "BUY_STOP", 
        "SELL_STOP", 
        "BUY_STOP_LIMIT", 
        "SELL_STOP_LIMIT"
    ]
    commission_report: CommissionReport