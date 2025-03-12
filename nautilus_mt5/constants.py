from decimal import Decimal
from typing import Final
from nautilus_trader.model.identifiers import Venue

MT5_VENUE: Final[Venue] = Venue("METATRADER_5")
NO_VALID_ID = -1
UNSET_DECIMAL = Decimal(2**127 - 1)