from decimal import Decimal
import functools
from typing import Tuple

from nautilus_trader.common.enums import LogColor
from nautilus_trader.model.position import Position

from nautilus_mt5.common import BaseMixin
from nautilus_mt5.data_types import MT5Position, MT5Symbol


class MetaTrader5ClientAccountMixin(BaseMixin):
    """
    Handles various account and position related requests for the
    MetaTrader5Client.

    Parameters
    ----------
    client : MetaTrader5Client
        The client instance that will be used to communicate with the Terminal API.

    """

    def accounts(self) -> set[str]:
        """
        Return a set of account identifiers managed by this instance.

        Returns
        -------
        set[str]

        """
        return self._account_ids.copy()

    def subscribe_account_summary(self) -> None:
        """
        Subscribe to the account summary for all accounts.

        It sends a request to MetaTrader 5 to retrieve account summary
        information.

        """

        name = "accountSummary"
        if not (subscription := self._subscriptions.get(name=name)):
            req_id = self._next_req_id()
            subscription = self._subscriptions.add(
                req_id=req_id,
                name=name,
                handle=functools.partial(
                    self._mt5_client.req_account_summary,
                    req_id=req_id,
                ),
                cancel=functools.partial(
                    self._mt5_client.cancel_account_summary,
                    req_id=req_id,
                ),
            )

        if not subscription:
            return

        subscription.handle()

    def unsubscribe_account_summary(self, account_id: str) -> None:
        """
        Unsubscribe from the account summary for the specified account.

        Parameters
        ----------
        account_id : str
            The identifier of the account to unsubscribe from.

        """
        name = "accountSummary"
        if subscription := self._subscriptions.get(name=name):
            self._subscriptions.remove(subscription.req_id)
            self._mt5_client.cancel_account_summary(req_id=subscription.req_id)
            self._log.debug(f"Unsubscribed from {subscription}")
        else:
            self._log.debug(f"Subscription doesn't exist for {name}")

    async def get_positions(self, account_id: str) -> list[Position] | None:
        """
        Fetch open positions for a specified account.

        Parameters
        ----------
        account_id: str
            The account identifier for which to fetch positions.

        Returns
        -------
        list[Position] | ``None``

        """
        self._log.debug(f"Requesting Open Positions for {account_id}")
        name = "OpenPositions"
        if not (request := self._requests.get(name=name)):
            request = self._requests.add(
                req_id=self._next_req_id(),
                name=name,
                handle=self._mt5_client.req_positions,
            )
            if not request:
                return None
            request.handle()
            all_positions = await self._await_request(request, 30)
        else:
            all_positions = await self._await_request(request, 30)
        if not all_positions:
            return None
        positions = []
        for position in all_positions:
            if position.account_id == account_id:
                positions.append(position)
        return positions

    async def process_account_summary(
        self,
        *,
        req_id: int,
        account_id: str,
        tag: str,
        value: str,
        currency: str,
    ) -> None:
        """
        Receive account information.
        """
        name = f"accountSummary-{account_id}"
        if handler := self._event_subscriptions.get(name, None):
            handler(tag, value, currency)

    async def process_managed_accounts(self, *, accounts: Tuple[str]) -> None:
        """
        Receive a tuple with the managed account ids.

        Occurs automatically on initial API client connection.

        """

        self._account_ids = set(accounts)  # {a for a in accounts_list.split(",") if a}
        self._log.debug(f"Managed accounts set: {self._account_ids}")

        if self._next_valid_order_id >= 0 and not self._is_mt5_connected.is_set():
            self._log.debug(
                "`_is_mt5_connected` set by `managed_accounts`.", LogColor.BLUE
            )
            self._is_mt5_connected.set()

    async def process_position(
        self,
        *,
        account_id: str,
        symbol: MT5Symbol,
        position: Decimal,
        avg_cost: float,
    ) -> None:
        """
        Provide the portfolio's open positions.
        """
        if request := self._requests.get(name="OpenPositions"):
            request.result.append(MT5Position(account_id, symbol, position, avg_cost))

    async def process_position_end(self) -> None:
        """
        Indicate that all the positions have been transmitted.
        """
        if request := self._requests.get(name="OpenPositions"):
            self._end_request(request.req_id)
