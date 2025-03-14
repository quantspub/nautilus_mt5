from collections.abc import Callable

import pandas as pd

from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.enums import TriggerType


MAP_TRIGGER_METHOD: dict[int, int] = {
    TriggerType.DEFAULT: 0,
    TriggerType.DOUBLE_BID_ASK: 1,
    TriggerType.LAST_PRICE: 2,
    TriggerType.DOUBLE_LAST: 3,
    TriggerType.BID_ASK: 4,
    TriggerType.LAST_OR_BID_ASK: 7,
    TriggerType.MID_POINT: 8,
}

MAP_TIME_IN_FORCE: dict[int, str] = {
    TimeInForce.DAY: "DAY",
    TimeInForce.GTC: "GTC",
    TimeInForce.IOC: "IOC",
    TimeInForce.GTD: "GTD",
    TimeInForce.AT_THE_OPEN: "OPG",
    TimeInForce.AT_THE_CLOSE: "DAY",
    TimeInForce.FOK: "FOK",
    # unsupported: 'DTC',
}

MAP_ORDER_ACTION: dict[int, str] = {
    OrderSide.BUY: "BUY",
    OrderSide.SELL: "SELL",
}

ORDER_SIDE_TO_ORDER_ACTION: dict[str, str] = {
    "BOT": "BUY",
    "SLD": "SELL",
}

MAP_ORDER_TYPE: dict[int | tuple[int, int], str] = {
    OrderType.LIMIT: "LMT",
    OrderType.LIMIT_IF_TOUCHED: "LIT",
    OrderType.MARKET: "MKT",
    OrderType.MARKET_IF_TOUCHED: "MIT",
    OrderType.MARKET_TO_LIMIT: "MTL",
    OrderType.STOP_LIMIT: "STP LMT",
    OrderType.STOP_MARKET: "STP",
    OrderType.TRAILING_STOP_LIMIT: "TRAIL LIMIT",
    OrderType.TRAILING_STOP_MARKET: "TRAIL",
    (OrderType.MARKET, TimeInForce.AT_THE_CLOSE): "MOC",
    (OrderType.LIMIT, TimeInForce.AT_THE_CLOSE): "LOC",
}


MAP_ORDER_FIELDS: set[tuple[str, str, Callable]] = {
    # ref: (nautilus_order_field, ib_order_field, value_fn)
    ("client_order_id", "orderRef", lambda x: x.value),
    ("display_qty", "displaySize", lambda x: x.as_double()),
    ("expire_time", "goodTillDate", lambda x: x.strftime("%Y%m%d %H:%M:%S %Z")),
    ("limit_offset", "lmtPriceOffset", float),
    ("order_type", "orderType", lambda x: MAP_ORDER_TYPE[x]),
    ("price", "lmtPrice", lambda x: x.as_double()),
    ("quantity", "totalQuantity", lambda x: x.as_decimal()),
    ("side", "action", lambda x: MAP_ORDER_ACTION[x]),
    ("time_in_force", "tif", lambda x: MAP_TIME_IN_FORCE[x]),
    # ("trailing_offset", "trailStopPrice", lambda x: float(x)),
    # ("trigger_price", "auxPrice", lambda x: x.as_double()),
    # ("trigger_type", "triggerMethod", lambda x: map_trigger_method[x]),
    ("parent_order_id", "parentId", lambda x: x.value),
}


MAP_ORDER_STATUS = {
    "ApiPending": OrderStatus.SUBMITTED,
    "PendingSubmit": OrderStatus.SUBMITTED,
    "PendingCancel": OrderStatus.PENDING_CANCEL,
    "PreSubmitted": OrderStatus.SUBMITTED,
    "Submitted": OrderStatus.ACCEPTED,
    "ApiCancelled": OrderStatus.CANCELED,
    "Cancelled": OrderStatus.CANCELED,
    "Filled": OrderStatus.FILLED,
    "Inactive": OrderStatus.DENIED,
}


def timestring_to_timestamp(timestring: str) -> pd.Timestamp:
    # Support string conversion not supported directly by pd.to_datetime
    # 20230223 00:43:36 America/New_York
    # 20230223 00:43:36 Universal
    dt, tz = timestring.rsplit(" ", 1)
    return pd.Timestamp(dt, tz=tz)
