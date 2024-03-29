import json
from typing import Any, Dict

import pytest

from doru.api.schema import Task, TaskCreate
from doru.exceptions import (
    DoruError,
    MoreThanMaxRunningTasks,
    OrderNotComplete,
    OrderNotCreated,
    OrderStatusUnknown,
    TaskDuplicate,
    TaskNotExist,
)
from doru.exchange import OrderStatus
from doru.manager.task_manager import TaskManager, create_task_manager, do_order

TEST_DATA = {
    "1": {
        "id": "1",
        "symbol": "BTC/JPY",
        "amount": 10000,
        "cycle": "Daily",
        "time": "00:00",
        "exchange": "bitbank",
        "status": "Running",
        "next_run": "2022-01-01 00:00",
    },
    "2": {
        "id": "2",
        "symbol": "ETH/JPY",
        "amount": 1000,
        "cycle": "Weekly",
        "weekday": "Mon",
        "time": "23:59",
        "exchange": "bitflyer",
        "status": "Stopped",
        "next_run": "2022-01-01 00:00",
    },
    "3": {
        "id": "3",
        "symbol": "ETH/JPY",
        "amount": 100,
        "cycle": "Monthly",
        "day": 28,
        "time": "23:59",
        "exchange": "bitflyer",
        "status": "Stopped",
        "next_run": "2022-01-01 00:00",
    },
}


@pytest.fixture
def task_file(tmpdir, tasks: Dict[str, Any]):
    file = tmpdir.mkdir("tmp").join("task.json")
    with open(file, "w") as fp:
        json.dump(tasks, fp)
    return file


@pytest.fixture
def task_manager(task_file) -> TaskManager:
    return create_task_manager(task_file)


@pytest.mark.parametrize("tasks", [TEST_DATA, {}])
def test_init_with_valid_task_file_succeed(task_file, tasks):
    m = create_task_manager(task_file)
    assert {k: v.dict(exclude_none=True) for (k, v) in m.tasks.items()} == tasks
    # Tasks with `Running` status should be submitted to threadpool
    for t in tasks.values():
        if t["status"] == "Running":
            assert t["id"] in m.pool.pool


def test_init_without_task_file_succeed(tmpdir, caplog):
    from logging import WARNING

    d = tmpdir.mkdir("tmp")
    file = f"{d}/task.json"
    m = create_task_manager(file)

    assert m.tasks == {}
    assert [
        ("doru.manager.task_manager", WARNING, "Task file for this application could not be found.")
    ] == caplog.record_tuples
    with open(m.file, "r") as f:
        assert json.load(f) == {}


def test_init_with_invalid_json_file_raise_exception(tmpdir):
    from pathlib import Path

    file = Path(tmpdir.mkdir("tmp").join("task.json"))
    file.touch()
    with pytest.raises(json.decoder.JSONDecodeError):
        create_task_manager(str(file))


@pytest.mark.parametrize(
    "tasks",
    [
        # without "id"
        {
            "1": {
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Daily",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # empty "id"
        {
            "1": {
                "id": "",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Daily",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # without "symbol"
        {
            "1": {
                "id": "1",
                "amount": 10000,
                "cycle": "Daily",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # invalid "symbol"
        {
            "1": {
                "id": "1",
                "symbol": "INVALID",
                "amount": 10000,
                "cycle": "Daily",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # without "amount"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "cycle": "Daily",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # less than 1 "amount"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 0,
                "cycle": "Daily",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # "amount" is not a number
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": "",
                "cycle": "Daily",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # without "cycle"
        {"1": {"id": "1", "symbol": "BTC/JPY", "amount": 10000, "exchange": "bitbank", "status": "Running"}},
        # invalid "cycle"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "min",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # without "weekday" when "cycle" is "Weekly"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Weekly",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # invalid "weekday" when "cycle" is "Weekly"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Weekly",
                "weekday": "Invalid",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # without "day" when "cycle" is "Monthly"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Monthly",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # invalid "day" when "cycle" is "Monthly"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Monthly",
                "day": 29,
                "time": "00:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # without "time"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Daily",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # invalid "time"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Daily",
                "time": "24:00",
                "exchange": "bitbank",
                "status": "Running",
            }
        },
        # without "exchange"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Daily",
                "time": "00:00",
                "status": "Running",
            }
        },
        # invalid "exchange"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Daily",
                "time": "00:00",
                "exchange": "invalid",
                "status": "Running",
            }
        },
        # without "status"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Daily",
                "time": "00:00",
                "exchange": "bitbank",
            }
        },
        # invalid "status"
        {
            "1": {
                "id": "1",
                "symbol": "BTC/JPY",
                "amount": 10000,
                "cycle": "Daily",
                "time": "00:00",
                "exchange": "bitbank",
                "status": "invalid",
            }
        },
    ],
)
def test_init_with_invalid_task_schema_raise_exception(tmpdir, tasks):
    file = tmpdir.mkdir("tmp").join("credential.json")
    with open(file, "w") as fp:
        json.dump(tasks, fp)
    with pytest.raises(Exception):
        create_task_manager(str(file))


@pytest.mark.parametrize("tasks", [TEST_DATA])
def test_init_with_exception_on_reading_raise_exception(task_file, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager._read", side_effect=Exception)
    with pytest.raises(Exception):
        create_task_manager(task_file)


@pytest.mark.parametrize("tasks", [TEST_DATA, {}])
def test_get_tasks_succeed(task_manager: TaskManager, tasks, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager._get_next_run", return_value="2022-01-01 00:00")
    t = task_manager.get_tasks()
    assert t == [Task.parse_obj(v) for v in tasks.values()]


@pytest.mark.parametrize("tasks", [TEST_DATA])
@pytest.mark.parametrize(
    "new_task", [TaskCreate(symbol="ETH/JPY", amount=1, cycle="Daily", time="00:00", exchange="bitbank")]
)
def test_add_task_with_valid_task_succeed(task_manager: TaskManager, tasks, new_task: TaskCreate):
    t = task_manager.add_task(new_task)
    assert (
        t.symbol == new_task.symbol
        and t.amount == new_task.amount
        and t.cycle == new_task.cycle
        and t.time == new_task.time
        and t.exchange == new_task.exchange
        and t.status == "Stopped"
    )
    result = {**tasks, **{t.id: t.dict(exclude_none=True)}}
    assert {k: v.dict(exclude_none=True) for (k, v) in task_manager.tasks.items()} == result
    with open(task_manager.file, "r") as f:
        assert json.load(f) == result


@pytest.mark.parametrize("tasks", [TEST_DATA])
@pytest.mark.parametrize(
    "new_task", [TaskCreate(symbol="ETH/JPY", amount=1, cycle="Daily", time="00:00", exchange="bitbank")]
)
def test_add_task_with_exception_on_writing_raise_exception(task_manager: TaskManager, tasks, new_task, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager._write", side_effect=Exception)
    with pytest.raises(Exception):
        task_manager.add_task(new_task)
    # assert add_task change nothing
    assert {k: v.dict(exclude_none=True) for (k, v) in task_manager.tasks.items()} == tasks
    with open(task_manager.file, "r") as f:
        assert json.load(f) == tasks


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "1")])
def test_remove_task_with_valid_id_succeed(task_manager: TaskManager, tasks, id):
    assert id in task_manager.pool.pool

    task_manager.remove_task(id)
    result = tasks.copy()
    result.pop(id)
    assert {k: v.dict(exclude_none=True) for (k, v) in task_manager.tasks.items()} == result
    assert id not in task_manager.pool.pool
    with open(task_manager.file, "r") as f:
        assert json.load(f) == result


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "123456789012")])
def test_remove_task_with_invalid_id_raise_exception(task_manager: TaskManager, tasks, id):
    with pytest.raises(Exception):
        task_manager.remove_task(id)
    # remove_task change nothing
    assert {k: v.dict(exclude_none=True) for (k, v) in task_manager.tasks.items()} == tasks
    with open(task_manager.file, "r") as f:
        assert json.load(f) == tasks


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "1")])
def test_remove_task_with_exception_on_writing_raise_exception(task_manager: TaskManager, tasks, id, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager._write", side_effect=Exception)
    with pytest.raises(Exception):
        task_manager.remove_task(id)
    # remove_task change nothing
    assert {k: v.dict(exclude_none=True) for (k, v) in task_manager.tasks.items()} == tasks
    assert id in task_manager.pool.pool
    with open(task_manager.file, "r") as f:
        assert json.load(f) == tasks


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "2")])
def test_start_task_with_valid_id_succeed(task_manager: TaskManager, id):
    assert id not in task_manager.pool.pool

    task_manager.start_task(id)

    assert id in task_manager.pool.pool
    assert task_manager.pool.pool[id].is_alive()
    assert task_manager.pool.pool[id].is_started()
    assert task_manager.tasks[id].status == "Running"
    with open(task_manager.file, "r") as f:
        assert json.load(f)[id]["status"] == "Running"


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "9999")])
def test_start_task_with_invalid_id_raise_exception(task_manager: TaskManager, tasks, id):
    with pytest.raises(TaskNotExist):
        task_manager.start_task(id)
    assert id not in task_manager.pool.pool
    assert {k: v.dict(exclude_none=True) for (k, v) in task_manager.tasks.items()} == tasks
    with open(task_manager.file, "r") as f:
        assert json.load(f) == tasks


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "1")])
def test_start_task_with_duplicate_id_raise_exception(task_manager: TaskManager, tasks, id):
    with pytest.raises(TaskDuplicate):
        task_manager.start_task(id)
    assert id in task_manager.pool.pool
    assert {k: v.dict(exclude_none=True) for (k, v) in task_manager.tasks.items()} == tasks
    with open(task_manager.file, "r") as f:
        assert json.load(f) == tasks


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "2")])
def test_start_task_with_exception_on_writing_raise_exception(task_manager: TaskManager, tasks, id, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager._write", side_effect=Exception)
    with pytest.raises(Exception):
        task_manager.start_task(id)
    assert id not in task_manager.pool.pool
    assert {k: v.dict(exclude_none=True) for (k, v) in task_manager.tasks.items()} == tasks
    with open(task_manager.file, "r") as f:
        assert json.load(f) == tasks


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "2")])
def test_start_task_more_than_max_running_tasks_raise_exception(task_file, tasks, id):
    m = create_task_manager(file=task_file, max_running_tasks=1)
    with pytest.raises(MoreThanMaxRunningTasks):
        m.start_task(id)
    assert id not in m.pool.pool
    assert {k: v.dict(exclude_none=True) for (k, v) in m.tasks.items()} == tasks
    with open(m.file, "r") as f:
        assert json.load(f) == tasks


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "1"), (TEST_DATA, "2")])
def test_stop_task_with_valid_id_succeed(task_manager: TaskManager, id):
    task_manager.stop_task(id)
    assert id not in task_manager.pool.pool
    assert task_manager.tasks[id].status == "Stopped"
    with open(task_manager.file, "r") as f:
        assert json.load(f)[id]["status"] == "Stopped"


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "9999")])
def test_stop_task_with_invalid_id_raise_exception(task_manager: TaskManager, tasks, id):
    with pytest.raises(TaskNotExist):
        task_manager.stop_task(id)
    assert {k: v.dict(exclude_none=True) for (k, v) in task_manager.tasks.items()} == tasks
    with open(task_manager.file, "r") as f:
        assert json.load(f) == tasks


@pytest.mark.parametrize("tasks, id", [(TEST_DATA, "1")])
def test_stop_task_with_exception_on_writing_raise_exception(task_manager: TaskManager, tasks, id, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager._write", side_effect=Exception)
    with pytest.raises(Exception):
        task_manager.stop_task(id)
    assert id in task_manager.pool.pool
    assert {k: v.dict(exclude_none=True) for (k, v) in task_manager.tasks.items()} == tasks
    with open(task_manager.file, "r") as f:
        assert json.load(f) == tasks


@pytest.mark.parametrize(
    "exchange_name,symbol,amount,order_status", [("binance", "BTC/USD", 100, OrderStatus.CLOSED.value)]
)
def test_do_order_return_none_when_order_complete(exchange_name, symbol, amount, order_status, mocker):
    mocker.patch("doru.exchange.Exchange.create_order", return_value="test_id")
    mocker.patch("doru.exchange.Exchange.wait_order_complete", return_value=order_status)
    result = do_order(exchange_name=exchange_name, symbol=symbol, amount=amount)
    assert result is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"symbol": "BTC/USD", "amount": 100},
        {"exchange_name": "binance", "amount": 100},
        {"exchange_name": "binance", "symbol": "BTC/USD"},
    ],
)
def test_do_order_raise_value_error_when_required_params_missing(kwargs):
    with pytest.raises(ValueError):
        do_order(**kwargs)


def test_do_order_raise_order_not_created_exception(mocker):
    mocker.patch("doru.exchange.Exchange.create_order", side_effect=Exception)
    with pytest.raises(OrderNotCreated):
        do_order(exchange_name="binance", symbol="BTC/USD", amount=100)


@pytest.mark.parametrize(
    "order_status", [OrderStatus.CANCELED.value, OrderStatus.EXPIRED.value, OrderStatus.REJECTED.value]
)
def test_do_order_raise_order_not_complete_exception(order_status, mocker):
    mocker.patch("doru.exchange.Exchange.create_order", return_value="test_id")
    mocker.patch("doru.exchange.Exchange.wait_order_complete", return_value=order_status)
    with pytest.raises(OrderNotComplete):
        do_order(exchange_name="binance", symbol="BTC/USD", amount=100)


@pytest.mark.parametrize("order_status", [None])
def test_do_order_raise_order_status_unknown_exception(order_status, mocker):
    mocker.patch("doru.exchange.Exchange.create_order", return_value="test_id")
    mocker.patch("doru.exchange.Exchange.wait_order_complete", return_value=order_status)
    with pytest.raises(OrderStatusUnknown):
        do_order(exchange_name="binance", symbol="BTC/USD", amount=100)


@pytest.mark.parametrize("order_status", [OrderStatus.OPEN.value])
def test_do_order_exception_when_order_status_is_open(order_status, mocker):
    mocker.patch("doru.exchange.Exchange.create_order", return_value="test_id")
    mocker.patch("doru.exchange.Exchange.wait_order_complete", return_value=order_status)
    mocker.patch("doru.exchange.Exchange.cancel_order", return_value=None)
    with pytest.raises(OrderNotComplete):
        do_order(exchange_name="binance", symbol="BTC/USD", amount=100)

    # fail to cancel the order for any reason
    mocker.patch("doru.exchange.Exchange.cancel_order", side_effect=Exception)
    with pytest.raises(DoruError):
        do_order(exchange_name="binance", symbol="BTC/USD", amount=100)
