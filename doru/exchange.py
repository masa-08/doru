import datetime
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import ccxt
from retry import retry
from typing_extensions import TypedDict

from doru.manager.credential_manager import create_credential_manager

logger = logging.getLogger(__name__)


class Precision(TypedDict):
    amount: int


class Market(TypedDict):
    symbol: str
    precision: Precision


class Ticker(TypedDict):
    symbol: str
    bid: Optional[float]
    last: float


class OrderStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"


class Exchange:
    _markets: Optional[Dict[str, Market]] = None

    def __init__(self, exchange: str) -> None:
        credential = self._read_credential(exchange)
        if not credential:
            logger.warning(f"Credential not found for {exchange}")
        self.exchange = self._get_exchange_instance(exchange, credential)

    @staticmethod
    def _read_credential(exchange: str) -> Dict[str, str]:
        manager = create_credential_manager()
        credential = manager.get_credential(exchange)
        return {"apiKey": credential.key, "secret": credential.secret} if credential is not None else {}

    @staticmethod
    def _get_exchange_instance(name: str, config: Dict[str, str]) -> ccxt.Exchange:
        exchange_class = getattr(ccxt, name, None)
        if exchange_class is None or not issubclass(exchange_class, ccxt.Exchange):
            raise ValueError(f"{name} is not supported.")
        return exchange_class(config)

    def _calc_amount(self, amount: float, precision: Optional[Union[int, float]]) -> float:
        # If precision is None, the calculation is performed with two significant digits.
        if precision is None:
            precision = 2
            counting_mode = ccxt.SIGNIFICANT_DIGITS
        else:
            counting_mode = self.exchange.precisionMode
        decimal = ccxt.decimal_to_precision(amount, precision=precision, counting_mode=counting_mode)
        return float(decimal)

    def _load_spot_markets(self) -> None:
        try:
            markets = self.exchange.fetch_markets()
        except Exception as e:
            logger.error(f"Failed to fetch markets: {e}")
            raise
        markets_dict: Dict[str, Market] = {}
        for m in markets:
            if m["type"] == "spot" and m["active"]:
                markets_dict[m["symbol"]] = {
                    "symbol": m["symbol"],
                    "precision": {"amount": m["precision"]["amount"]},
                }
        self._markets = markets_dict

    def _fetch_ticker(self, symbol: str) -> Ticker:
        raw_ticker: Dict[str, Any] = self.exchange.fetch_ticker(symbol)
        return {"symbol": raw_ticker["symbol"], "bid": raw_ticker["bid"], "last": raw_ticker["last"]}

    def fetch_spot_symbols(self) -> List[str]:
        try:
            self._load_spot_markets()
        except Exception as e:
            logger.error(f"Failed to fetch symbols: {e}")
            raise
        return list(self._markets.keys()) if self._markets else []

    def create_order(self, symbol: str, quote_amount: float) -> str:
        try:
            ticker = self._fetch_ticker(symbol)
            bid = ticker["bid"] or ticker["last"]  # because sometimes bid is None
            self._load_spot_markets()
            if self._markets is None:
                raise Exception("Failed to load markets.")
            amount = self._calc_amount(quote_amount / bid, self._markets[symbol]["precision"]["amount"])
            result = self.exchange.create_order(symbol=symbol, type="limit", side="buy", amount=amount, price=bid)
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            raise
        return result["id"]

    def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        try:
            result = self.exchange.fetch_order(order_id, symbol)
        except Exception as e:
            logger.error(f"Failed to fecth order: {e}")
            raise
        return result

    def wait_order_complete(
        self,
        order_id: str,
        symbol: str,
        wait_for: datetime.timedelta = datetime.timedelta(minutes=15),
        tick: float = 60,
    ) -> Optional[str]:
        result: Optional[Dict[str, Any]] = None
        start = datetime.datetime.now()
        while True:
            try:
                result = self.fetch_order(order_id, symbol)
            except Exception:
                # Ignore errors because we want to continue processing even when order rtrieval may
                # fail for unforeseen reasons
                pass
            else:
                if result["status"] == OrderStatus.CLOSED.value:
                    logger.info(f"Completed order: {result}")
                    break
                elif result["status"] in (
                    OrderStatus.CANCELED.value,
                    OrderStatus.EXPIRED.value,
                    OrderStatus.REJECTED.value,
                ):
                    logger.error(f"The order is no longer valid: {result}")
                    break
            finally:
                time.sleep(tick)

            if datetime.datetime.now() - start > wait_for:
                break

        if result is None:
            logger.error("The order status is unknown")
            return None
        if result["status"] == OrderStatus.OPEN.value:
            logger.error(f"The order was not completed: {result}")
        return result["status"]

    @retry(tries=5, delay=2)
    def cancel_order(self, order_id: str, symbol: str) -> None:
        try:
            self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise


def get_exchange(name: str) -> Exchange:
    return Exchange(name)
