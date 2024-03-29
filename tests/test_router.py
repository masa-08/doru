import json
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from doru.api.app import create_app
from doru.manager.credential_manager import CredentialManager, create_credential_manager
from doru.manager.task_manager import TaskManager, create_task_manager

TASK_DATA = {
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
}
CREDENTIAL_DATA = {
    "bitbank": {
        "key": "bitbank_key",
        "secret": "bitbank_secret",
    },
}

app = create_app()


@pytest.fixture
def task_file(tmpdir, tasks: Dict[str, Any]):
    file = tmpdir.mkdir("tmp").join("task.json")
    with open(file, "w") as fp:
        json.dump(tasks, fp)
    return file


@pytest.fixture
def task_manager(task_file) -> TaskManager:
    return create_task_manager(task_file)


@pytest.fixture
def credential_file(tmpdir, credentials: Dict[str, Any]):
    file = tmpdir.mkdir("tmp").join("credential.json")
    with open(file, "w") as fp:
        json.dump(credentials, fp)
    return file


@pytest.fixture
def credential_manager(credential_file) -> CredentialManager:
    return create_credential_manager(credential_file)


@pytest.mark.parametrize("tasks", [TASK_DATA, {}])
def test_get_tasks_succeed(task_manager, tasks, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager._get_next_run", return_value="2022-01-01 00:00")
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.get("/tasks")
        assert res.is_success
        assert res.json() == list(tasks.values())


@pytest.mark.parametrize("tasks", [TASK_DATA])
@pytest.mark.parametrize(
    "new_task",
    [
        {"symbol": "ETH/JPY", "amount": 1, "cycle": "Daily", "time": "00:00", "exchange": "bitbank"},
        {
            "symbol": "ETH/JPY",
            "amount": 1,
            "cycle": "Daily",
            "time": "00:00",
            "exchange": "bitbank",
            "foo": "bar",
        },  # extra key-value
    ],
)
def test_post_task_with_valid_body_succeed(task_manager, new_task):
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post("/tasks", json=new_task)
        data = res.json()
        assert res.is_success
        assert data["symbol"] == new_task["symbol"]
        assert data["amount"] == new_task["amount"]
        assert data["cycle"] == new_task["cycle"]
        assert data["exchange"] == new_task["exchange"]
        assert data["status"] == "Stopped"

        new_id = data["id"]
        res = client.get("/tasks")
        assert new_id in [d["id"] for d in res.json()]


@pytest.mark.parametrize(
    "new_task",
    [
        # without symbol
        {"amount": 1, "cycle": "1Monthly", "exchange": "bitbank"},
        # invalid symbol
        {"symbol": "INVALID", "amount": 1, "cycle": "1Monthly", "exchange": "bitbank"},
        # without amount
        {"symbol": "ETH/JPY", "cycle": "1Monthly", "exchange": "bitbank"},
        # invalid amount
        {"symbol": "ETH/JPY", "amount": 0, "cycle": "1Monthly", "exchange": "bitbank"},
        # invalid amount
        {"symbol": "ETH/JPY", "amount": "invalid", "cycle": "1Monthly", "exchange": "bitbank"},
        # without cycle
        {"symbol": "ETH/JPY", "amount": 1, "exchange": "bitbank"},
        # invalid cycle
        {"symbol": "ETH/JPY", "amount": 1, "cycle": "invalid", "exchange": "bitbank"},
        # without exchange
        {"symbol": "ETH/JPY", "amount": 1, "cycle": "1Monthly"},
        # invalid exchange
        {"symbol": "ETH/JPY", "amount": 1, "cycle": "1Monthly", "exchange": "invalid"},
    ],
)
@pytest.mark.parametrize("tasks", [TASK_DATA])
def test_post_task_with_invalid_body_fail(task_manager, new_task):
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post("/tasks", json=new_task)
        assert res.is_error


@pytest.mark.parametrize(
    "new_task",
    [{"symbol": "ETH/JPY", "amount": 1, "cycle": "Daily", "time": "00:00", "exchange": "bitbank"}],
)
@pytest.mark.parametrize("tasks", [TASK_DATA])
def test_post_task_with_unexpected_error_fail(task_manager, new_task, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager.add_task", side_effect=Exception)
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post("/tasks", json=new_task)
        assert res.is_error
        assert res.json()["detail"] == "An internal error has occurred."


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "2")])
def test_post_start_task_with_valid_id_succeed(task_manager, id):
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post(f"/tasks/{id}/start")
        assert res.is_success

        res = client.get("/tasks")
        task = next((d for d in res.json() if d["id"] == id))
        assert task["status"] == "Running"


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "1")])
def test_post_start_task_with_duplicate_id_fail(task_manager, id):
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post(f"/tasks/{id}/start")
        assert res.is_error
        assert res.json()["detail"] == f"The task with ID {id} has already started."


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "9999")])
def test_post_start_task_with_nonexistent_id_fail(task_manager, id):
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post(f"/tasks/{id}/start")
        assert res.is_error
        assert res.json()["detail"] == f"The task ID {id} does not exist."


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "2")])
def test_post_start_task_exceed_max_running_tasks_fail(task_file, id):
    task_manager = create_task_manager(file=task_file, max_running_tasks=1)
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post(f"/tasks/{id}/start")
        assert res.is_error
        assert res.json()["detail"] == "The maximum number of tasks(1) that can be executed has been exceeded."


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "2")])
def test_post_start_task_with_unexpected_error_fail(task_manager, id, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager.start_task", side_effect=Exception)
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post(f"/tasks/{id}/start")
        assert res.is_error
        assert res.json()["detail"] == "An internal error has occurred."


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "1")])
def test_post_stop_task_with_valid_id_succeed(task_manager, id):
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post(f"/tasks/{id}/stop")
        assert res.is_success

        res = client.get("/tasks")
        task = next((d for d in res.json() if d["id"] == id))
        assert task["status"] == "Stopped"


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "2")])
def test_post_stop_task_with_stopped_task_id_succeed(task_manager, id):
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post(f"/tasks/{id}/stop")
        assert res.is_success

        res = client.get("/tasks")
        task = next((d for d in res.json() if d["id"] == id))
        assert task["status"] == "Stopped"


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "9999")])
def test_post_stop_task_with_nonexistent_id_fail(task_manager, id):
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post(f"/tasks/{id}/stop")
        assert res.is_error
        assert res.json()["detail"] == f"The task ID {id} does not exist."


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "1")])
def test_post_stop_task_with_unexpected_error_fail(task_manager, id, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager.stop_task", side_effect=Exception)
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.post(f"/tasks/{id}/stop")
        assert res.is_error
        assert res.json()["detail"] == "An internal error has occurred."


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "1")])
def test_delete_task_with_valid_id_succeed(task_manager, id):
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.delete(f"/tasks/{id}")
        assert res.is_success

        res = client.get("/tasks")
        assert id not in [d["id"] for d in res.json()]


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "9999")])
def test_delete_task_with_invalid_id_fail(task_manager, id):
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.delete(f"/tasks/{id}")
        assert res.is_error
        assert res.json()["detail"] == f"The task ID {id} does not exist."


@pytest.mark.parametrize("tasks, id", [(TASK_DATA, "1")])
def test_delete_task_with_unexpected_error_fail(task_manager, id, mocker):
    mocker.patch("doru.manager.task_manager.TaskManager.remove_task", side_effect=Exception)
    with app.container.task_manager.override(task_manager):
        client = TestClient(app)
        res = client.delete(f"/tasks/{id}")
        assert res.is_error
        assert res.json()["detail"] == "An internal error has occurred."


@pytest.mark.parametrize("credentials", [CREDENTIAL_DATA])
@pytest.mark.parametrize(
    "new_cred",
    [
        {"exchange": "bitflyer", "key": "bitflyer_key", "secret": "bitflyer_secret"},  # new exchange
        {"exchange": "bitflyer", "key": "bitflyer_key", "secret": "bitflyer_secret", "foo": "bar"},  # extra key-value
        {"exchange": "bitbank", "key": "new_bitbank_key", "secret": "new_bitbank_secret"},  # override
    ],
)
def test_post_credential_with_valid_body_succeed(credential_manager, new_cred):
    with app.container.credential_manager.override(credential_manager):
        client = TestClient(app)
        res = client.post("/credentials", json=new_cred)
        assert res.is_success


@pytest.mark.parametrize("credentials", [CREDENTIAL_DATA])
@pytest.mark.parametrize(
    "new_cred",
    [
        {"key": "bitflyer_key", "secret": "bitflyer_secret"},  # without exchange
        {"exchange": "invalid", "key": "bitflyer_key", "secret": "bitflyer_secret"},  # invalid exchange
        {"exchange": "bitflyer", "secret": "bitflyer_secret"},  # without key
        {"exchange": "bitflyer", "key": "bitflyer_key"},  # without secret
    ],
)
def test_post_credential_with_invalid_body_fail(credential_manager, new_cred):
    with app.container.credential_manager.override(credential_manager):
        client = TestClient(app)
        res = client.post("/credentials", json=new_cred)
        assert res.is_error


@pytest.mark.parametrize("credentials", [CREDENTIAL_DATA])
@pytest.mark.parametrize(
    "new_cred",
    [
        {"exchange": "bitflyer", "key": "bitflyer_key", "secret": "bitflyer_secret"},  # new exchange
    ],
)
def test_post_credential_with_unexpected_error_fail(credential_manager, new_cred, mocker):
    mocker.patch("doru.manager.credential_manager.CredentialManager.add_credential", side_effect=Exception)
    with app.container.credential_manager.override(credential_manager):
        client = TestClient(app)
        res = client.post("/credentials", json=new_cred)
        assert res.is_error
        assert res.json()["detail"] == "An internal error has occurred."


@pytest.mark.parametrize("credentials, exchange", [(CREDENTIAL_DATA, "bitbank")])
def test_delete_credential_with_valid_exchange_succeed(credential_manager, exchange):
    with app.container.credential_manager.override(credential_manager):
        client = TestClient(app)
        res = client.delete(f"/credentials/{exchange}")
        assert res.is_success


@pytest.mark.parametrize("credentials, exchange", [(CREDENTIAL_DATA, "bitflyer")])
def test_delete_credential_with_nonexistent_exchange_fail(credential_manager, exchange):
    with app.container.credential_manager.override(credential_manager):
        client = TestClient(app)
        res = client.delete(f"/credentials/{exchange}")
        assert res.is_error
        assert res.json()["detail"] == f"The credential of {exchange} does not exist."


@pytest.mark.parametrize("credentials, exchange", [(CREDENTIAL_DATA, "bitbank")])
def test_delete_credential_with_unexpected_error_fail(credential_manager, exchange, mocker):
    mocker.patch("doru.manager.credential_manager.CredentialManager.remove_credential", side_effect=Exception)
    with app.container.credential_manager.override(credential_manager):
        client = TestClient(app)
        res = client.delete(f"/credentials/{exchange}")
        assert res.is_error
        assert res.json()["detail"] == "An internal error has occurred."
