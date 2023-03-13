import logging
import os

import ccxt
import pytest

from doru.exchange import Exchange, get_exchange

EXCHANGE_NAME = os.environ.get("EXCHANGE", "binance")
EXCHANGE_APIKEY = os.environ.get("EXCHANGE_APIKEY", "")
EXCHANGE_SECRET = os.environ.get("EXCHANGE_SECRET", "")


MARKETS_VALUE = [
    {
        "id": "btcusd",
        "symbol": "BTC/USD",
        "base": "BTC",
        "quote": "USD",
        "baseId": "btc",
        "quoteId": "usd",
        "active": True,
        "type": "spot",
        "spot": True,
        "margin": True,
        "future": False,
        "swap": False,
        "option": False,
        "contract": False,
        "settle": "USDT",
        "settleId": "usdt",
        "contractSize": 1,
        "linear": True,
        "inverse": False,
        "expiry": 1641370465121,
        "expiryDatetime": "2022-03-26T00:00:00.000Z",
        "strike": 4000,
        "optionType": "call",
        "taker": 0.002,
        "maker": 0.0016,
        "percentage": True,
        "tierBased": False,
        "feeSide": "get",
        "precision": {
            "price": 8,
            "amount": 8,
            "cost": 8,
        },
        "limits": {
            "amount": {
                "min": 0.01,
                "max": 1000,
            },
            "price": {...},
            "cost": {...},
            "leverage": {...},
        },
        "info": {...},
    },
    {
        "id": "ethusd",
        "symbol": "ETH/USD",
        "base": "ETH",
        "quote": "USD",
        "baseId": "eth",
        "quoteId": "usd",
        "active": True,
        "type": "spot",
        "spot": True,
        "margin": True,
        "future": False,
        "swap": False,
        "option": False,
        "contract": False,
        "settle": "USDT",
        "settleId": "usdt",
        "contractSize": 1,
        "linear": True,
        "inverse": False,
        "expiry": 1641370465121,
        "expiryDatetime": "2022-03-26T00:00:00.000Z",
        "strike": 4000,
        "optionType": "call",
        "taker": 0.002,
        "maker": 0.0016,
        "percentage": True,
        "tierBased": False,
        "feeSide": "get",
        "precision": {
            "price": 8,
            "amount": 8,
            "cost": 8,
        },
        "limits": {
            "amount": {
                "min": 0.01,
                "max": 1000,
            },
            "price": {...},
            "cost": {...},
            "leverage": {...},
        },
        "info": {...},
    },
    {
        "id": "btcusd_nonspot",
        "symbol": "BTC/USD",
        "base": "BTC",
        "quote": "USD",
        "baseId": "btc",
        "quoteId": "usd",
        "active": True,
        "type": "future",  # non-spot type
        "spot": True,
        "margin": True,
        "future": False,
        "swap": False,
        "option": False,
        "contract": False,
        "settle": "USDT",
        "settleId": "usdt",
        "contractSize": 1,
        "linear": True,
        "inverse": False,
        "expiry": 1641370465121,
        "expiryDatetime": "2022-03-26T00:00:00.000Z",
        "strike": 4000,
        "optionType": "call",
        "taker": 0.002,
        "maker": 0.0016,
        "percentage": True,
        "tierBased": False,
        "feeSide": "get",
        "precision": {
            "price": 8,
            "amount": 8,
            "cost": 8,
        },
        "limits": {
            "amount": {
                "min": 0.01,
                "max": 1000,
            },
            "price": {...},
            "cost": {...},
            "leverage": {...},
        },
        "info": {...},
    },
    {
        "id": "btcusd_notactive",
        "symbol": "BTC/USD",
        "base": "BTC",
        "quote": "USD",
        "baseId": "btc",
        "quoteId": "usd",
        "active": False,  # not active
        "type": "spot",
        "spot": True,
        "margin": True,
        "future": False,
        "swap": False,
        "option": False,
        "contract": False,
        "settle": "USDT",
        "settleId": "usdt",
        "contractSize": 1,
        "linear": True,
        "inverse": False,
        "expiry": 1641370465121,
        "expiryDatetime": "2022-03-26T00:00:00.000Z",
        "strike": 4000,
        "optionType": "call",
        "taker": 0.002,
        "maker": 0.0016,
        "percentage": True,
        "tierBased": False,
        "feeSide": "get",
        "precision": {
            "price": 8,
            "amount": 8,
            "cost": 8,
        },
        "limits": {
            "amount": {
                "min": 0.01,
                "max": 1000,
            },
            "price": {...},
            "cost": {...},
            "leverage": {...},
        },
        "info": {...},
    },
]


TICKER_VALUE = {
    "symbol": "BTC/USD:BTC",
    "timestamp": 1678794752218,
    "datetime": "2023-03-14T11:52:32.218Z",
    "high": 24928.0,
    "low": 21998.2,
    "bid": 24816.7,
    "bidVolume": None,
    "ask": None,
    "askVolume": None,
    "vwap": 23896.57787891,
    "open": 22132.2,
    "close": 24816.7,
    "last": 24816.7,
    "previousClose": None,
    "change": 2684.5,
    "percentage": 12.129,
    "average": 23474.45,
    "baseVolume": 212628.31128989,
    "quoteVolume": 50810890.0,
    "info": {
        "symbol": "BTCUSD_PERP",
        "pair": "BTCUSD",
        "priceChange": "2684.5",
        "priceChangePercent": "12.129",
        "weightedAvgPrice": "23896.57787891",
        "lastPrice": "24816.7",
        "lastQty": "1",
        "openPrice": "22132.2",
        "highPrice": "24928.0",
        "lowPrice": "21998.2",
        "volume": "50810890",
        "baseVolume": "212628.31128989",
        "openTime": "1678708320000",
        "closeTime": "1678794752218",
        "firstId": "598857806",
        "lastId": "599970451",
        "count": "1112610",
    },
}
TICKER_VALUE_2 = {
    "symbol": "BTC/USD:BTC",
    "timestamp": 1678794752218,
    "datetime": "2023-03-14T11:52:32.218Z",
    "high": 24928.0,
    "low": 21998.2,
    "bid": None,  # bid is None
    "bidVolume": None,
    "ask": None,
    "askVolume": None,
    "vwap": 23896.57787891,
    "open": 22132.2,
    "close": 24816.7,
    "last": 24816.7,
    "previousClose": None,
    "change": 2684.5,
    "percentage": 12.129,
    "average": 23474.45,
    "baseVolume": 212628.31128989,
    "quoteVolume": 50810890.0,
    "info": {
        "symbol": "BTCUSD_PERP",
        "pair": "BTCUSD",
        "priceChange": "2684.5",
        "priceChangePercent": "12.129",
        "weightedAvgPrice": "23896.57787891",
        "lastPrice": "24816.7",
        "lastQty": "1",
        "openPrice": "22132.2",
        "highPrice": "24928.0",
        "lowPrice": "21998.2",
        "volume": "50810890",
        "baseVolume": "212628.31128989",
        "openTime": "1678708320000",
        "closeTime": "1678794752218",
        "firstId": "598857806",
        "lastId": "599970451",
        "count": "1112610",
    },
}


@pytest.fixture
def exchange(mocker):
    mocker.patch(
        "doru.exchange.Exchange._read_credential", return_value={"apiKey": EXCHANGE_APIKEY, "secret": EXCHANGE_SECRET}
    )
    mocker.patch("doru.exchange.Exchange._get_exchange_instance", return_value=ccxt.Exchange())
    return get_exchange(EXCHANGE_NAME)


def test_init_with_valid_exchange_name_succeed(mocker):
    mocker.patch("doru.exchange.Exchange._read_credential", return_value={"key": "", "secret": ""})
    exchange = Exchange("binance")
    assert isinstance(exchange.exchange, ccxt.Exchange)

    # Check if the precisionMode adopted by each exchange is set
    assert exchange.exchange.precisionMode == ccxt.DECIMAL_PLACES
    exchange = Exchange("bitfinex")
    assert exchange.exchange.precisionMode == ccxt.SIGNIFICANT_DIGITS
    exchange = Exchange("okx")
    assert exchange.exchange.precisionMode == ccxt.TICK_SIZE


def test_init_with_invalid_exchange_name_fail(mocker):
    mocker.patch("doru.exchange.Exchange._read_credential", return_value={"key": "", "secret": ""})
    with pytest.raises(ValueError):
        Exchange("invalid_exchange")


@pytest.mark.parametrize("target", ["binance"])
def test_init_warn_without_credential(mocker, caplog, target):
    mocker.patch("doru.manager.credential_manager.CredentialManager.get_credential", return_value=None)
    exchange = Exchange(target)
    assert ("doru.exchange", logging.WARNING, f"Credential not found for {target}") in caplog.record_tuples
    assert isinstance(exchange.exchange, ccxt.Exchange)


@pytest.mark.parametrize(
    "amount,precision,mode,expected",
    [
        (1249.99999999, None, ccxt.SIGNIFICANT_DIGITS, 1200.0),
        (1250.00000001, None, ccxt.SIGNIFICANT_DIGITS, 1300.0),
        (1249.99988888, 8, ccxt.SIGNIFICANT_DIGITS, 1249.9999),
        (1249.99988888, 13, ccxt.SIGNIFICANT_DIGITS, 1249.99988888),
        (1249.99988888, 4, ccxt.DECIMAL_PLACES, 1249.9999),
        (1248.88888888, 0, ccxt.DECIMAL_PLACES, 1249.0),
        (1249.99988888, 9, ccxt.DECIMAL_PLACES, 1249.99988888),
        (1249.99988888, 0.0001, ccxt.TICK_SIZE, 1249.9999),
        (1248.88888888, 1, ccxt.TICK_SIZE, 1249.0),
        (1249.99988888, 0.000000001, ccxt.TICK_SIZE, 1249.99988888),
    ],
)
def test_calc_amount_without_digit(exchange, amount, precision, mode, expected):
    exchange.exchange.precisionMode = mode
    assert exchange._calc_amount(amount, precision) == expected


def test_fetch_spot_symbols(exchange: Exchange, mocker):
    mocker.patch("ccxt.Exchange.fetch_markets", return_value=MARKETS_VALUE)
    symbols = exchange.fetch_spot_symbols()
    assert "BTC/USD" in symbols and "ETH/USD" in symbols
    # assert only active spot type loaded
    assert exchange._markets is not None and exchange._markets == {
        "BTC/USD": {"symbol": "BTC/USD", "precision": {"amount": 8}},
        "ETH/USD": {"symbol": "ETH/USD", "precision": {"amount": 8}},
    }

    mocker.patch("ccxt.Exchange.fetch_markets", side_effect=Exception)
    with pytest.raises(Exception):
        exchange.fetch_spot_symbols()


def test_create_order_succeed(exchange: Exchange, mocker):
    mocker.patch("ccxt.Exchange.fetch_ticker", return_value=TICKER_VALUE)
    mocker.patch("ccxt.Exchange.fetch_markets", return_value=MARKETS_VALUE)
    mocker.patch("ccxt.Exchange.create_order", return_value={"id": "hogehoge"})
    spy = mocker.spy(ccxt.Exchange, "create_order")
    result = exchange.create_order("BTC/USD", 1000)
    # We don't want to actually throw a request to the exchange,
    # so just check if ccxt.Exchange.create_order is called
    assert spy.call_count == 1
    assert result == "hogehoge"

    # assert that the order can be placed even if the bid is None
    mocker.patch("ccxt.Exchange.fetch_ticker", return_value=TICKER_VALUE_2)
    result = exchange.create_order("BTC/USD", 1000)
    assert spy.call_count == 2


def test_create_order_fail_with_exception(exchange: Exchange, mocker):
    mocker.patch("ccxt.Exchange.fetch_ticker", return_value=TICKER_VALUE)
    mocker.patch("ccxt.Exchange.fetch_markets", return_value=[])
    with pytest.raises(Exception):
        exchange.create_order("BTC/USD", 1000)


@pytest.mark.parametrize(
    "status,log",
    [
        ("closed", "Completed order:"),
        ("canceled", "The order is no longer valid:"),
        ("expired", "The order is no longer valid:"),
        ("rejected", "The order is no longer valid:"),
        ("open", "The order was not completed:"),
    ],
)
def test_wait_order_complete(exchange: Exchange, status, log, mocker, caplog):
    import datetime

    mocker.patch("ccxt.Exchange.fetch_order", return_value={"status": status})
    caplog.set_level(logging.INFO)

    result = exchange.wait_order_complete("hogehoge", "BTC/USD", datetime.timedelta(seconds=3), tick=1)
    assert result == status
    assert log in caplog.text

    mocker.patch("ccxt.Exchange.fetch_order", side_effect=Exception)
    with pytest.raises(Exception):
        exchange.wait_order_complete("hogehoge", "BTC/USD", datetime.timedelta(seconds=3), tick=1)
