import asyncio
import json
from decimal import Decimal
from typing import Any

import pandas as pd

from nautilus_mt5.common import CommissionReport
from nautilus_mt5.common import (
    UNSET_DECIMAL,
    UNSET_DOUBLE,
)  # TODO: remove dependency
from nautilus_mt5.execution import Execution
from nautilus_mt5.order import Order as MT5Order
from nautilus_mt5.order import OrderState as MT5OrderState

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.core.rust.common import LogColor
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.messages import BatchCancelOrders
from nautilus_trader.execution.messages import CancelAllOrders
from nautilus_trader.execution.messages import CancelOrder
from nautilus_trader.execution.messages import ModifyOrder
from nautilus_trader.execution.messages import SubmitOrder
from nautilus_trader.execution.messages import SubmitOrderList
from nautilus_trader.execution.reports import FillReport
from nautilus_trader.execution.reports import OrderStatusReport
from nautilus_trader.execution.reports import PositionStatusReport
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import LiquiditySide
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.enums import TrailingOffsetType
from nautilus_trader.model.enums import TriggerType
from nautilus_trader.model.enums import trailing_offset_type_to_str
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import AccountBalance
from nautilus_trader.model.objects import Currency
from nautilus_trader.model.objects import MarginBalance
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders.base import Order
from nautilus_trader.model.orders.limit_if_touched import LimitIfTouchedOrder
from nautilus_trader.model.orders.market_if_touched import MarketIfTouchedOrder
from nautilus_trader.model.orders.stop_limit import StopLimitOrder
from nautilus_trader.model.orders.stop_market import StopMarketOrder
from nautilus_trader.model.orders.trailing_stop_limit import TrailingStopLimitOrder
from nautilus_trader.model.orders.trailing_stop_market import TrailingStopMarketOrder

from mt5 import MetaTrader5Ext as MetaTrader5Client
from nautilus_mt5.client.common import MT5Position
from nautilus_mt5.common import MT5_VENUE
from nautilus_mt5.common import MT5OrderTags
from nautilus_mt5.config import MetaTrader5ExecClientConfig
from nautilus_mt5.parsing.execution import MAP_ORDER_ACTION
from nautilus_mt5.parsing.execution import MAP_ORDER_FIELDS
from nautilus_mt5.parsing.execution import MAP_ORDER_STATUS
from nautilus_mt5.parsing.execution import MAP_ORDER_TYPE
from nautilus_mt5.parsing.execution import MAP_TIME_IN_FORCE
from nautilus_mt5.parsing.execution import MAP_TRIGGER_METHOD
from nautilus_mt5.parsing.execution import ORDER_SIDE_TO_ORDER_ACTION
from nautilus_mt5.parsing.execution import timestring_to_timestamp
from nautilus_mt5.providers import MetaTrader5InstrumentProvider


mt5_to_nautilus_trigger_method = dict(
    zip(MAP_TRIGGER_METHOD.values(), MAP_TRIGGER_METHOD.keys(), strict=False),
)
mt5_to_nautilus_time_in_force = dict(
    zip(MAP_TIME_IN_FORCE.values(), MAP_TIME_IN_FORCE.keys(), strict=False),
)
mt5_to_nautilus_order_side = dict(
    zip(MAP_ORDER_ACTION.values(), MAP_ORDER_ACTION.keys(), strict=False),
)
mt5_to_nautilus_order_type = dict(
    zip(MAP_ORDER_TYPE.values(), MAP_ORDER_TYPE.keys(), strict=False)
)


class MetaTrader5ExecutionClient(LiveExecutionClient):
    """
    Provides an execution client for MetaTrader 5 Terminal API, allowing for the
    retrieval of account information and execution of orders.

    Parameters
    ----------
    loop : asyncio.AbstractEventLoop
        The event loop for the client.
    client : MetaTrader5Client
        The nautilus MetaTrader5Client using ibapi.
    account_id: AccountId
        Account ID associated with this client.
    msgbus : MessageBus
        The message bus for the client.
    cache : Cache
        The cache for the client.
    clock : LiveClock
        The clock for the client.
    instrument_provider : MetaTrader5InstrumentProvider
        The instrument provider.
    config : MetaTrader5ExecClientConfig, optional
        The configuration for the instance.
    name : str, optional
        The custom client ID.

    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client: MetaTrader5Client,
        account_id: AccountId,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        instrument_provider: MetaTrader5InstrumentProvider,
        config: MetaTrader5ExecClientConfig,
        name: str | None = None,
    ) -> None:
        super().__init__(
            loop=loop,
            client_id=ClientId(name or f"{MT5_VENUE.value}"),
            venue=MT5_VENUE,
            oms_type=OmsType.NETTING,
            instrument_provider=instrument_provider,
            account_type=AccountType.MARGIN,
            base_currency=None,  # IB accounts are multi-currency | TODO: change this to USD
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
        )
        self._client: MetaTrader5Client = client
        self._set_account_id(account_id)
        self._account_summary_tags = {
            "NetLiquidation",
            "FullAvailableFunds",
            "FullInitMarginReq",
            "FullMaintMarginReq",
        }

        self._account_summary_loaded: asyncio.Event = asyncio.Event()

        # Hot caches
        self._account_summary: dict[str, dict[str, Any]] = {}

    @property
    def instrument_provider(self) -> MetaTrader5InstrumentProvider:
        return self._instrument_provider  # type: ignore

    async def _connect(self):
        # Connect client
        await self._client.wait_until_ready()
        await self.instrument_provider.initialize()

        # Validate if connected to expected Terminal using Account
        if self.account_id.get_id() in self._client.accounts():
            self._log.info(
                f"Account `{self.account_id.get_id()}` found in the connected Terminal.",
                LogColor.GREEN,
            )
        else:
            self.fault()
            raise ValueError(
                f"Account `{self.account_id.get_id()}` not found in the connected Terminal. "
                f"Available accounts are {self._client.accounts()}",
            )

        # Event hooks
        account = self.account_id.get_id()
        self._client.registered_nautilus_clients.add(self.id)
        self._client.subscribe_event(
            f"accountSummary-{account}", self._on_account_summary
        )
        self._client.subscribe_event(f"openOrder-{account}", self._on_open_order)
        self._client.subscribe_event(f"orderStatus-{account}", self._on_order_status)
        self._client.subscribe_event(f"execDetails-{account}", self._on_exec_details)

        # Load account balance
        self._client.subscribe_account_summary()
        await self._account_summary_loaded.wait()

        self._set_connected(True)

    async def _disconnect(self):
        self._client.registered_nautilus_clients.discard(self.id)
        if (
            self._client.is_running
            and self._client.registered_nautilus_clients == set()
        ):
            self._client.stop()
        self._set_connected(False)

    async def generate_order_status_report(
        self,
        instrument_id: InstrumentId,
        client_order_id: ClientOrderId | None = None,
        venue_order_id: VenueOrderId | None = None,
    ) -> OrderStatusReport | None:
        """
        Generate an `OrderStatusReport` for the given order identifier parameter(s). If
        the order is not found, or an error occurs, then logs and returns ``None``.

        Parameters
        ----------
        instrument_id : InstrumentId
            The instrument ID for the report.
        client_order_id : ClientOrderId, optional
            The client order ID for the report.
        venue_order_id : VenueOrderId, optional
            The venue order ID for the report.

        Returns
        -------
        OrderStatusReport or ``None``

        Raises
        ------
        ValueError
            If both the `client_order_id` and `venue_order_id` are ``None``.

        """
        PyCondition.type_or_none(client_order_id, ClientOrderId, "client_order_id")
        PyCondition.type_or_none(venue_order_id, VenueOrderId, "venue_order_id")
        if not (client_order_id or venue_order_id):
            self._log.debug(
                "Both `client_order_id` and `venue_order_id` cannot be None."
            )
            return None

        report = None
        mt5_orders = await self._client.get_open_orders(self.account_id.get_id())
        for mt5_order in mt5_orders:
            if (client_order_id and client_order_id.value == mt5_order.orderRef) or (
                venue_order_id
                and venue_order_id.value
                == str(
                    mt5_order.order_id,
                )
            ):
                report = await self._parse_mt5_order_to_order_status_report(mt5_order)
                break
        if report is None:
            self._log.warning(
                f"Order {client_order_id=}, {venue_order_id} not found, Cancelling...",
            )
            self._on_order_status(
                order_ref=client_order_id.value,
                order_status="Cancelled",
                reason="Not found in query",
            )
        return report

    async def _parse_mt5_order_to_order_status_report(
        self, mt5_order: MT5Order
    ) -> OrderStatusReport:
        self._log.debug(f"Trying OrderStatusReport for {mt5_order.__dict__}")
        instrument = await self.instrument_provider.find_with_symbol_id(
            mt5_order.contract.sym_id,
        )

        total_qty = (
            Quantity.from_int(0)
            if mt5_order.totalQuantity == UNSET_DECIMAL
            else Quantity.from_str(str(mt5_order.totalQuantity))
        )
        filled_qty = (
            Quantity.from_int(0)
            if mt5_order.filledQuantity == UNSET_DECIMAL
            else Quantity.from_str(str(mt5_order.filledQuantity))
        )
        if total_qty.as_double() > filled_qty.as_double() > 0:
            order_status = OrderStatus.PARTIALLY_FILLED
        else:
            order_status = MAP_ORDER_STATUS[mt5_order.order_state.status]
        ts_init = self._clock.timestamp_ns()
        price = (
            None
            if mt5_order.lmtPrice == UNSET_DOUBLE
            else instrument.make_price(mt5_order.lmtPrice)
        )
        expire_time = (
            timestring_to_timestamp(mt5_order.goodTillDate)
            if mt5_order.tif == "GTD"
            else None
        )

        mapped_order_type_info = mt5_to_nautilus_order_type[mt5_order.orderType]
        if isinstance(mapped_order_type_info, tuple):
            order_type, time_in_force = mapped_order_type_info
        else:
            order_type = mapped_order_type_info
            time_in_force = mt5_to_nautilus_time_in_force[mt5_order.tif]

        order_status = OrderStatusReport(
            account_id=self.account_id,
            instrument_id=instrument.id,
            venue_order_id=VenueOrderId(str(mt5_order.order_id)),
            order_side=mt5_to_nautilus_order_side[mt5_order.action],
            order_type=order_type,
            time_in_force=time_in_force,
            order_status=order_status,
            quantity=total_qty,
            filled_qty=Quantity.from_int(0),
            avg_px=Decimal(0),
            report_id=UUID4(),
            ts_accepted=ts_init,
            ts_last=ts_init,
            ts_init=ts_init,
            client_order_id=ClientOrderId(mt5_order.orderRef),
            # order_list_id=,
            # contingency_type=,
            expire_time=expire_time,
            price=price,
            trigger_price=instrument.make_price(mt5_order.auxPrice),
            trigger_type=TriggerType.BID_ASK,
            # limit_offset=,
            # trailing_offset=,
        )
        self._log.debug(f"Received {order_status!r}")
        return order_status

    async def generate_order_status_reports(
        self,
        instrument_id: InstrumentId | None = None,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
        open_only: bool = False,
    ) -> list[OrderStatusReport]:
        """
        Generate a list of `OrderStatusReport`s with optional query filters. The
        returned list may be empty if no orders match the given parameters.

        Parameters
        ----------
        instrument_id : InstrumentId, optional
            The instrument ID query filter.
        start : pd.Timestamp, optional
            The start datetime (UTC) query filter.
        end : pd.Timestamp, optional
            The end datetime (UTC) query filter.
        open_only : bool, default False
            If the query is for open orders only.

        Returns
        -------
        list[OrderStatusReport]

        """
        report = []
        # Create the Filled OrderStatusReport from Open Positions
        positions: list[MT5Position] = await self._client.get_positions(
            self.account_id.get_id(),
        )
        if not positions:
            return []
        ts_init = self._clock.timestamp_ns()
        for position in positions:
            self._log.debug(
                f"Infer OrderStatusReport from open position {position.contract.__dict__}",
            )
            if position.quantity > 0:
                order_side = OrderSide.BUY
            elif position.quantity < 0:
                order_side = OrderSide.SELL
            else:
                continue  # Skip, IB may continue to display closed positions

            instrument = await self.instrument_provider.find_with_symbol_id(
                position.contract.sym_id,
            )
            if instrument is None:
                self._log.error(
                    f"Cannot generate report: instrument not found for contract ID {position.contract.sym_id}",
                )
                continue

            avg_px = instrument.make_price(
                position.avg_cost / instrument.multiplier,
            ).as_decimal()
            quantity = Quantity.from_str(str(position.quantity.copy_abs()))
            order_status = OrderStatusReport(
                account_id=self.account_id,
                instrument_id=instrument.id,
                venue_order_id=VenueOrderId(instrument.id.value),
                order_side=order_side,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.FOK,
                order_status=OrderStatus.FILLED,
                quantity=quantity,
                filled_qty=quantity,
                avg_px=avg_px,
                report_id=UUID4(),
                ts_accepted=ts_init,
                ts_last=ts_init,
                ts_init=ts_init,
                client_order_id=ClientOrderId(instrument.id.value),
            )
            self._log.debug(f"Received {order_status!r}")
            report.append(order_status)

        # Create the Open OrderStatusReport from Open Orders
        mt5_orders: list[MT5Order] = await self._client.get_open_orders(
            self.account_id.get_id(),
        )
        for mt5_order in mt5_orders:
            order_status = await self._parse_mt5_order_to_order_status_report(mt5_order)
            report.append(order_status)
        return report

    async def generate_fill_reports(
        self,
        instrument_id: InstrumentId | None = None,
        venue_order_id: VenueOrderId | None = None,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> list[FillReport]:
        """
        Generate a list of `FillReport`s with optional query filters. The returned list
        may be empty if no trades match the given parameters.

        Parameters
        ----------
        instrument_id : InstrumentId, optional
            The instrument ID query filter.
        venue_order_id : VenueOrderId, optional
            The venue order ID (assigned by the venue) query filter.
        start : pd.Timestamp, optional
            The start datetime (UTC) query filter.
        end : pd.Timestamp, optional
            The end datetime (UTC) query filter.

        Returns
        -------
        list[FillReport]

        """
        self._log.warning("Cannot generate `list[FillReport]`: not yet implemented.")

        return []  # TODO: Implement

    async def generate_position_status_reports(
        self,
        instrument_id: InstrumentId | None = None,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> list[PositionStatusReport]:
        """
        Generate a list of `PositionStatusReport`s with optional query filters. The
        returned list may be empty if no positions match the given parameters.

        Parameters
        ----------
        instrument_id : InstrumentId, optional
            The instrument ID query filter.
        start : pd.Timestamp, optional
            The start datetime (UTC) query filter.
        end : pd.Timestamp, optional
            The end datetime (UTC) query filter.

        Returns
        -------
        list[PositionStatusReport]

        """
        report = []
        positions: list[MT5Position] | None = await self._client.get_positions(
            self.account_id.get_id(),
        )
        if not positions:
            return []
        for position in positions:
            self._log.debug(
                f"Trying PositionStatusReport for {position.contract.sym_id}"
            )
            if position.quantity > 0:
                side = PositionSide.LONG
            elif position.quantity < 0:
                side = PositionSide.SHORT
            else:
                continue  # Skip, IB may continue to display closed positions

            instrument = await self.instrument_provider.find_with_symbol_id(
                position.contract.sym_id,
            )
            if instrument is None:
                self._log.error(
                    f"Cannot generate report: instrument not found for contract ID {position.contract.sym_id}",
                )
                continue

            if not self._cache.instrument(instrument.id):
                self._handle_data(instrument)

            position_status = PositionStatusReport(
                account_id=self.account_id,
                instrument_id=instrument.id,
                position_side=side,
                quantity=Quantity.from_str(str(abs(position.quantity))),
                report_id=UUID4(),
                ts_last=self._clock.timestamp_ns(),
                ts_init=self._clock.timestamp_ns(),
            )
            self._log.debug(f"Received {position_status!r}")
            report.append(position_status)

        return report

    def _transform_order_to_mt5_order(
        self, order: Order
    ) -> MT5Order:  # noqa: C901 11 > 10
        if order.is_post_only:
            raise ValueError("`post_only` not supported by Interactive Brokers")

        mt5_order = MT5Order()
        time_in_force = order.time_in_force
        for key, field, fn in MAP_ORDER_FIELDS:
            if value := getattr(order, key, None):
                if key == "order_type" and time_in_force == TimeInForce.AT_THE_CLOSE:
                    setattr(mt5_order, field, fn((value, time_in_force)))
                else:
                    setattr(mt5_order, field, fn(value))

        if self._cache.instrument(order.instrument_id).is_inverse:
            mt5_order.cashQty = int(mt5_order.totalQuantity)
            mt5_order.totalQuantity = 0

        if isinstance(order, TrailingStopLimitOrder | TrailingStopMarketOrder):
            if order.trailing_offset_type != TrailingOffsetType.PRICE:
                raise ValueError(
                    f"`TrailingOffsetType` {trailing_offset_type_to_str(order.trailing_offset_type)} is not supported",
                )

            mt5_order.auxPrice = float(order.trailing_offset)
            if order.trigger_price:
                mt5_order.trailStopPrice = order.trigger_price.as_double()
                mt5_order.triggerMethod = MAP_TRIGGER_METHOD[order.trigger_type]
        elif (
            isinstance(
                order,
                MarketIfTouchedOrder
                | LimitIfTouchedOrder
                | StopLimitOrder
                | StopMarketOrder,
            )
        ) and order.trigger_price:
            mt5_order.auxPrice = order.trigger_price.as_double()

        details = self.instrument_provider.contract_details[order.instrument_id.value]
        mt5_order.contract = details.contract
        mt5_order.account = self.account_id.get_id()
        mt5_order.clearingAccount = self.account_id.get_id()

        if order.tags:
            return self._attach_order_tags(mt5_order, order)
        else:
            return mt5_order

    def _attach_order_tags(self, mt5_order: MT5Order, order: Order) -> MT5Order:
        tags: dict = {}
        for ot in order.tags:
            if ot.startswith("MT5OrderTags:"):
                tags = MT5OrderTags.parse(ot.replace("MT5OrderTags:", "")).dict()
                break

        for tag in tags:
            if tag == "conditions":
                for condition in tags[tag]:
                    pass  # TODO:
            else:
                setattr(mt5_order, tag, tags[tag])

        return mt5_order

    async def _submit_order(self, command: SubmitOrder) -> None:
        PyCondition.type(command, SubmitOrder, "command")
        try:
            mt5_order: MT5Order = self._transform_order_to_mt5_order(command.order)
            mt5_order.order_id = self._client.next_order_id()
            self._client.place_order(mt5_order)
            self._handle_order_event(status=OrderStatus.SUBMITTED, order=command.order)
        except ValueError as e:
            self._handle_order_event(
                status=OrderStatus.REJECTED,
                order=command.order,
                reason=str(e),
            )

    async def _submit_order_list(self, command: SubmitOrderList) -> None:
        PyCondition.type(command, SubmitOrderList, "command")

        order_id_map = {}
        client_id_to_orders = {}
        mt5_orders = []

        # Translate orders
        for order in command.order_list.orders:
            order_id_map[order.client_order_id.value] = self._client.next_order_id()
            client_id_to_orders[order.client_order_id.value] = order

            try:
                mt5_order = self._transform_order_to_mt5_order(order)
                mt5_order.transmit = False
                mt5_order.order_id = order_id_map[order.client_order_id.value]
                mt5_orders.append(mt5_order)
            except ValueError as e:
                # All orders in the list are declined to prevent unintended side effects
                for o in command.order_list.orders:
                    if o == order:
                        self._handle_order_event(
                            status=OrderStatus.REJECTED,
                            order=command.order,
                            reason=str(e),
                        )
                    else:
                        self._handle_order_event(
                            status=OrderStatus.REJECTED,
                            order=command.order,
                            reason=f"The order has been rejected due to the rejection of the order with "
                            f"{order.client_order_id!r} in the list",
                        )
                return

        # Mark last order to transmit
        mt5_orders[-1].transmit = True

        for mt5_order in mt5_orders:
            # Map the Parent Order Ids
            if parent_id := order_id_map.get(mt5_order.parentId):
                mt5_order.parentId = parent_id
            # Place orders
            order_ref = mt5_order.orderRef
            self._client.place_order(mt5_order)
            self._handle_order_event(
                status=OrderStatus.SUBMITTED,
                order=client_id_to_orders[order_ref],
            )

    async def _modify_order(self, command: ModifyOrder) -> None:
        PyCondition.not_none(command, "command")
        if not (command.quantity or command.price or command.trigger_price):
            return

        nautilus_order: Order = self._cache.order(command.client_order_id)
        self._log.info(f"Nautilus order status is {nautilus_order.status_string()}")
        try:
            mt5_order: MT5Order = self._transform_order_to_mt5_order(nautilus_order)
        except ValueError as e:
            self._handle_order_event(
                status=OrderStatus.REJECTED,
                order=command.order,
                reason=str(e),
            )
            return

        mt5_order.order_id = int(command.venue_order_id.value)
        if mt5_order.parentId:
            parent_nautilus_order = self._cache.order(ClientOrderId(mt5_order.parentId))
            if parent_nautilus_order:
                mt5_order.parentId = int(parent_nautilus_order.venue_order_id.value)
            else:
                mt5_order.parentId = 0
        if command.quantity and command.quantity != mt5_order.totalQuantity:
            mt5_order.totalQuantity = command.quantity.as_double()
        if command.price and command.price.as_double() != getattr(
            mt5_order, "lmtPrice", None
        ):
            mt5_order.lmtPrice = command.price.as_double()
        if command.trigger_price and command.trigger_price.as_double() != getattr(
            mt5_order,
            "auxPrice",
            None,
        ):
            mt5_order.auxPrice = command.trigger_price.as_double()
        self._log.info(f"Placing {mt5_order!r}")
        self._client.place_order(mt5_order)

    async def _cancel_order(self, command: CancelOrder) -> None:
        PyCondition.not_none(command, "command")

        venue_order_id = command.venue_order_id
        if venue_order_id:
            self._client.cancel_order(int(venue_order_id.value))
        else:
            self._log.error(f"VenueOrderId not found for {command.client_order_id}")

    async def _cancel_all_orders(self, command: CancelAllOrders) -> None:
        for order in self._cache.orders_open(
            instrument_id=command.instrument_id,
        ):
            venue_order_id = order.venue_order_id
            if venue_order_id:
                self._client.cancel_order(int(venue_order_id.value))
            else:
                self._log.error(f"VenueOrderId not found for {order.client_order_id}")

    async def _batch_cancel_orders(self, command: BatchCancelOrders) -> None:
        for order in command.cancels:
            await self._cancel_order(order)

    def _on_account_summary(self, tag: str, value: str, currency: str) -> None:
        if not self._account_summary.get(currency):
            self._account_summary[currency] = {}
        try:
            self._account_summary[currency][tag] = float(value)
        except ValueError:
            self._account_summary[currency][tag] = value

        for currency in self._account_summary:
            if not currency:
                continue
            if (
                self._account_summary_tags - set(self._account_summary[currency].keys())
                == set()
            ):
                self._log.info(f"{self._account_summary}", LogColor.GREEN)
                # free = self._account_summary[currency]["FullAvailableFunds"]
                locked = self._account_summary[currency]["FullMaintMarginReq"]
                total = self._account_summary[currency]["NetLiquidation"]
                if total - locked < locked:
                    total = 400000  # TODO: Bug; Cannot recalculate balance when no current balance
                free = total - locked
                account_balance = AccountBalance(
                    total=Money(total, Currency.from_str(currency)),
                    free=Money(free, Currency.from_str(currency)),
                    locked=Money(locked, Currency.from_str(currency)),
                )

                margin_balance = MarginBalance(
                    initial=Money(
                        self._account_summary[currency]["FullInitMarginReq"],
                        currency=Currency.from_str(currency),
                    ),
                    maintenance=Money(
                        self._account_summary[currency]["FullMaintMarginReq"],
                        currency=Currency.from_str(currency),
                    ),
                )

                self.generate_account_state(
                    balances=[account_balance],
                    margins=[margin_balance],
                    reported=True,
                    ts_event=self._clock.timestamp_ns(),
                )

                # Store all available fields to Cache (for now until permanent solution)
                self._cache.add(
                    f"accountSummary:{self.account_id.get_id()}",
                    json.dumps(self._account_summary).encode("utf-8"),
                )

        self._account_summary_loaded.set()

    def _handle_order_event(  # noqa: C901
        self,
        status: OrderStatus,
        order: Order,
        order_id: int | None = None,
        reason: str = "",
    ) -> None:
        if status == OrderStatus.SUBMITTED:
            self.generate_order_submitted(
                strategy_id=order.strategy_id,
                instrument_id=order.instrument_id,
                client_order_id=order.client_order_id,
                ts_event=self._clock.timestamp_ns(),
            )
        elif status == OrderStatus.ACCEPTED:
            if order.status != OrderStatus.ACCEPTED:
                self.generate_order_accepted(
                    strategy_id=order.strategy_id,
                    instrument_id=order.instrument_id,
                    client_order_id=order.client_order_id,
                    venue_order_id=VenueOrderId(str(order_id)),
                    ts_event=self._clock.timestamp_ns(),
                )
            else:
                self._log.debug(f"Order {order.client_order_id} already accepted.")
        elif status == OrderStatus.FILLED:
            if order.status != OrderStatus.FILLED:
                # TODO: self.generate_order_filled
                self._log.debug(f"Order {order.client_order_id} is filled.")
        elif status == OrderStatus.PENDING_CANCEL:
            # TODO: self.generate_order_pending_cancel
            self._log.warning(f"Order {order.client_order_id} is {status.name}")
        elif status == OrderStatus.CANCELED:
            if order.status != OrderStatus.CANCELED:
                self.generate_order_canceled(
                    strategy_id=order.strategy_id,
                    instrument_id=order.instrument_id,
                    client_order_id=order.client_order_id,
                    venue_order_id=order.venue_order_id,
                    ts_event=self._clock.timestamp_ns(),
                )
        elif status == OrderStatus.REJECTED:
            if order.status != OrderStatus.REJECTED:
                self.generate_order_rejected(
                    strategy_id=order.strategy_id,
                    instrument_id=order.instrument_id,
                    client_order_id=order.client_order_id,
                    reason=reason,
                    ts_event=self._clock.timestamp_ns(),
                )
        else:
            self._log.warning(
                f"Order {order.client_order_id} with status={status.name} is unknown or "
                "not yet implemented.",
            )

    async def handle_order_status_report(self, mt5_order: MT5Order) -> None:
        report = await self._parse_mt5_order_to_order_status_report(mt5_order)
        self._send_order_status_report(report)

    def _on_open_order(
        self, order_ref: str, order: MT5Order, order_state: MT5OrderState
    ) -> None:
        if not order.orderRef:
            self._log.warning(
                f"ClientOrderId not available, order={order.__dict__}, state={order_state.__dict__}",
            )
            return
        if not (nautilus_order := self._cache.order(ClientOrderId(order_ref))):
            self.create_task(self.handle_order_status_report(order))
            return

        if order.whatIf and order_state.status == "PreSubmitted":
            # TODO: Is there more better approach for this use case?
            # This tells the details about Pre and Post margin changes, user can request by setting whatIf flag
            # order will not be placed by IB and instead returns simulation.
            # example={'status': 'PreSubmitted', 'initMarginBefore': '52.88', 'maintMarginBefore': '52.88', 'equityWithLoanBefore': '23337.31', 'initMarginChange': '2517.5099999999998', 'maintMarginChange': '2517.5099999999998', 'equityWithLoanChange': '-0.6200000000026193', 'initMarginAfter': '2570.39', 'maintMarginAfter': '2570.39', 'equityWithLoanAfter': '23336.69', 'commission': 2.12362, 'minCommission': 1.7976931348623157e+308, 'maxCommission': 1.7976931348623157e+308, 'commissionCurrency': 'USD', 'warningText': '', 'completedTime': '', 'completedStatus': ''}  # noqa
            self._handle_order_event(
                status=OrderStatus.REJECTED,
                order=nautilus_order,
                reason=json.dumps({"whatIf": order_state.__dict__}),
            )
        elif order_state.status in [
            "PreSubmitted",
            "Submitted",
        ]:
            instrument = self.instrument_provider.find(nautilus_order.instrument_id)
            total_qty = (
                Quantity.from_int(0)
                if order.totalQuantity == UNSET_DECIMAL
                else Quantity.from_str(str(order.totalQuantity))
            )
            price = (
                None
                if order.lmtPrice == UNSET_DOUBLE
                else instrument.make_price(order.lmtPrice)
            )
            trigger_price = (
                None
                if order.auxPrice == UNSET_DOUBLE
                else instrument.make_price(order.auxPrice)
            )
            venue_order_id_modified = bool(
                nautilus_order.venue_order_id is None
                or nautilus_order.venue_order_id != VenueOrderId(str(order.order_id)),
            )

            if total_qty != nautilus_order.quantity or price or trigger_price:
                self.generate_order_updated(
                    strategy_id=nautilus_order.strategy_id,
                    instrument_id=nautilus_order.instrument_id,
                    client_order_id=nautilus_order.client_order_id,
                    venue_order_id=VenueOrderId(str(order.order_id)),
                    quantity=total_qty,
                    price=price,
                    trigger_price=trigger_price,
                    ts_event=self._clock.timestamp_ns(),
                    venue_order_id_modified=venue_order_id_modified,
                )
            self._handle_order_event(
                status=OrderStatus.ACCEPTED,
                order=nautilus_order,
                order_id=order.order_id,
            )

    def _on_order_status(
        self, order_ref: str, order_status: str, reason: str = ""
    ) -> None:
        if order_status in ["ApiCancelled", "Cancelled"]:
            status = OrderStatus.CANCELED
        elif order_status == "PendingCancel":
            status = OrderStatus.PENDING_CANCEL
        elif order_status == "Rejected":
            status = OrderStatus.REJECTED
        elif order_status == "Filled":
            status = OrderStatus.FILLED
        elif order_status == "Inactive":
            self._log.warning(
                f"Order status is 'Inactive' because it is invalid or triggered an error for {order_ref=}",
            )
            return
        elif order_status in ["PreSubmitted", "Submitted"]:
            self._log.debug(
                f"Ignoring `_on_order_status` event for {order_status=} is handled in `_on_open_order`",
            )
            return
        else:
            self._log.warning(
                f"Unknown {order_status=} received on `_on_order_status` for {order_ref=}",
            )
            return

        nautilus_order = self._cache.order(ClientOrderId(order_ref))
        if nautilus_order:
            self._handle_order_event(
                status=status,
                order=nautilus_order,
                reason=reason,
            )
        else:
            self._log.warning(f"ClientOrderId {order_ref} not found in Cache")

    def _on_exec_details(
        self,
        order_ref: str,
        execution: Execution,
        commission_report: CommissionReport,
    ) -> None:
        if not execution.orderRef:
            self._log.warning(
                f"ClientOrderId not available, order={execution.__dict__}"
            )
            return
        if not (nautilus_order := self._cache.order(ClientOrderId(order_ref))):
            self._log.warning(
                f"ClientOrderId not found in Cache, order={execution.__dict__}"
            )
            return

        instrument = self.instrument_provider.find(nautilus_order.instrument_id)

        if instrument:
            self.generate_order_filled(
                strategy_id=nautilus_order.strategy_id,
                instrument_id=nautilus_order.instrument_id,
                client_order_id=nautilus_order.client_order_id,
                venue_order_id=VenueOrderId(str(execution.order_id)),
                venue_position_id=None,
                trade_id=TradeId(execution.execId),
                order_side=OrderSide[ORDER_SIDE_TO_ORDER_ACTION[execution.side]],
                order_type=nautilus_order.order_type,
                last_qty=Quantity(
                    execution.shares, precision=instrument.size_precision
                ),
                last_px=Price(execution.price, precision=instrument.price_precision),
                quote_currency=instrument.quote_currency,
                commission=Money(
                    commission_report.commission,
                    Currency.from_str(commission_report.currency),
                ),
                liquidity_side=LiquiditySide.NO_LIQUIDITY_SIDE,
                ts_event=timestring_to_timestamp(execution.time).value,
            )
