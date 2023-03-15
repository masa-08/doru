from typing import Any, Dict, List, Union

import pytest

from doru.api.client import create_client
from doru.api.schema import Task

TEST_DATA: List[Task] = [
    Task(
        id="1",
        exchange="bitbank",
        cycle="Daily",
        time="00:00",
        amount=10000,
        symbol="BTC/JPY",
        status="Stopped",
    ),
    Task(
        id="2",
        cycle="Weekly",
        weekday="Mon",
        time="23:59",
        exchange="bitflyer",
        amount=20000,
        symbol="ETH/JPY",
        status="Running",
    ),
    Task(
        id="3",
        cycle="Monthly",
        day=28,
        time="23:59",
        exchange="bitflyer",
        amount=30000,
        symbol="ETH/JPY",
        status="Stopped",
    ),
]


class MockResponse:
    def __init__(self, data: Union[List[Dict[str, Any]], Dict[str, Any]], status_code: int) -> None:
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data

    def raise_for_status(self):
        pass


def test_get_tasks_with_empty_value_succeed(mocker):
    def get_response(*args, **kwargs):
        return MockResponse([], 200)

    mocker.patch("doru.api.session.SessionWithSocket.get", side_effect=get_response)
    d = create_client()
    result = d.get_tasks()
    assert result == []


def test_get_tasks_with_not_empty_value_succeed(mocker):
    def get_response(*args, **kwargs):
        return MockResponse([d.dict() for d in TEST_DATA], 200)

    mocker.patch("doru.api.session.SessionWithSocket.get", side_effect=get_response)
    d = create_client()
    result = d.get_tasks()
    assert result == TEST_DATA


def test_get_tasks_with_extra_key_succeed(mocker):
    def get_response(*args, **kwargs):
        return MockResponse([{"extra": "value", **d.dict()} for d in TEST_DATA], 200)

    mocker.patch("doru.api.session.SessionWithSocket.get", side_effect=get_response)
    d = create_client()
    result = d.get_tasks()
    assert result == TEST_DATA


def test_get_tasks_with_missing_required_key_fail(mocker):
    def get_response(*args, **kwargs):
        return MockResponse([{k: v for k, v in d.dict().items() if k != "id"} for d in TEST_DATA], 200)

    mocker.patch("doru.api.session.SessionWithSocket.get", side_effect=get_response)
    d = create_client()
    with pytest.raises(KeyError) as e:
        d.get_tasks()
    assert e


@pytest.mark.parametrize("exchange, cycle, time, amount, symbol", [["bitbank", "Daily", "00:00", 1, "BTC/JPY"]])
def test_add_task_with_valid_response_succeed(exchange, cycle, time, amount, symbol, mocker):
    def get_response(*args, **kwargs):
        return MockResponse(TEST_DATA[0].dict(), 200)

    mocker.patch("doru.api.session.SessionWithSocket.post", side_effect=get_response)
    d = create_client()
    result = d.add_task(exchange, cycle, time, amount, symbol)
    assert result == TEST_DATA[0]


@pytest.mark.parametrize("exchange, cycle, time, amount, symbol", [["bitbank", "Daily", "00:00", 1, "BTC/JPY"]])
def test_add_task_with_empty_response_fail(exchange, cycle, time, amount, symbol, mocker):
    def get_response(*args, **kwargs):
        return MockResponse({}, 200)

    mocker.patch("doru.api.session.SessionWithSocket.post", side_effect=get_response)
    d = create_client()
    with pytest.raises(KeyError) as e:
        d.add_task(exchange, cycle, time, amount, symbol)
    assert e


@pytest.mark.parametrize("exchange, cycle, time, amount, symbol", [["bitbank", "Daily", "00:00", 1, "BTC/JPY"]])
def test_add_task_with_extra_key_succeed(exchange, cycle, time, amount, symbol, mocker):
    def get_response(*args, **kwargs):
        return MockResponse({"extra": "value", **TEST_DATA[0].dict()}, 200)

    mocker.patch("doru.api.session.SessionWithSocket.post", side_effect=get_response)
    d = create_client()
    result = d.add_task(exchange, cycle, time, amount, symbol)
    assert result == TEST_DATA[0]


@pytest.mark.parametrize("exchange, cycle, time, amount, symbol", [["bitbank", "Daily", "00:00", 1, "BTC/JPY"]])
def test_add_task_with_missing_required_key_fail(exchange, cycle, time, amount, symbol, mocker):
    def get_response(*args, **kwargs):
        return MockResponse({k: v for k, v in TEST_DATA[0].dict().items() if k != "id"}, 200)

    mocker.patch("doru.api.session.SessionWithSocket.post", side_effect=get_response)
    d = create_client()
    with pytest.raises(KeyError) as e:
        d.add_task(exchange, cycle, time, amount, symbol)
    assert e
