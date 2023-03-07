import logging
import os

import ccxt
import pytest

from doru.exchange import Exchange, get_exchange

EXCHANGE_NAME = os.environ.get("EXCHANGE", "")
EXCHANGE_APIKEY = os.environ.get("EXCHANGE_APIKEY", "")
EXCHANGE_SECRET = os.environ.get("EXCHANGE_SECRET", "")


@pytest.fixture
def exchange(mocker):
    mocker.patch(
        "doru.exchange.Exchange._read_credential", return_value={"apiKey": EXCHANGE_APIKEY, "secret": EXCHANGE_SECRET}
    )
    return get_exchange(EXCHANGE_NAME)


def test_init_with_valid_exchange_name_succeed(mocker):
    mocker.patch("doru.exchange.Exchange._read_credential", return_value={"key": "", "secret": ""})
    exchange = Exchange("binance")
    assert isinstance(exchange.exchange, ccxt.Exchange)


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


@pytest.mark.skip
def test_fetch_spot_symbols(exchange: Exchange):
    symbols = exchange.fetch_spot_symbols()
    assert "BTC/JPY" in symbols


@pytest.mark.skip
def test_create_order(exchange: Exchange):
    order_id = exchange.create_order("BTC/JPY", 5000)
    assert order_id


@pytest.mark.skip
def test_wait_order_complete(exchange: Exchange):
    order_id = exchange.create_order("BTC/JPY", 5000)
    assert exchange.wait_order_complete(order_id, "BTC/JPY") == "closed"


@pytest.mark.skip
def test_wait_order_complete_open(exchange: Exchange, mocker):
    # Daring to set a bid that is unlikely to be executed
    mocker.patch("doru.exchange.Exchange._fetch_ticker", return_value={"bid": 2000000})
    order_id = exchange.create_order("BTC/JPY", 2000)
    assert exchange.wait_order_complete(order_id, "BTC/JPY") == "open"


@pytest.mark.skip
def test_cancel_order(exchange: Exchange, mocker):
    # Daring to set a bid that is unlikely to be executed
    mocker.patch("doru.exchange.Exchange._fetch_ticker", return_value={"bid": 2000000})
    order_id = exchange.create_order("BTC/JPY", 2000)
    exchange.cancel_order(order_id, "BTC/JPY")
    assert exchange.exchange.fetch_order_status(order_id, "BTC/JPY") == "canceled"
