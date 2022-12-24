from typing import List

import pytest
from click.testing import CliRunner

from doru.api.schema import Task
from doru.cli import cli
from doru.daemon_manager import DaemonManager

TEST_DATA: List[Task] = [
    Task(
        id="1",
        exchange="bitbank",
        interval="1day",
        amount=10000,
        pair="BTC_JPY",
        status="Stopped",
    ),
    Task(
        id="2",
        interval="1week",
        exchange="bitflyer",
        amount=20000,
        pair="ETH_JPY",
        status="Running",
    ),
]


@pytest.mark.parametrize("exchange, interval, amount, pair", [["bitbank", "1day", "1", "BTC_JPY"]])
def test_add_with_valid_amount_succeed(exchange, interval, amount, pair, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.add_task", return_value=TEST_DATA[1])
    mocker.patch("doru.daemon_manager.DaemonManager.start_task", return_value=None)
    spy = mocker.spy(DaemonManager, "start_task")
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-i", interval, "-a", amount, "-p", pair])
    assert result.exit_code == 0
    assert spy.call_count == 1


@pytest.mark.parametrize("exchange, interval, amount, pair, start", [["bitbank", "1day", "1", "BTC_JPY", "False"]])
def test_add_with_valid_amount_and_not_start_flag_succeed(exchange, interval, amount, pair, start, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.add_task", return_value=TEST_DATA[1])
    spy = mocker.spy(DaemonManager, "start_task")
    result = CliRunner().invoke(
        cli, args=["add", "-e", exchange, "-i", interval, "-a", amount, "-p", pair, "-s", start]
    )
    assert result.exit_code == 0
    assert spy.call_count == 0


@pytest.mark.parametrize("exchange, interval, amount, pair", [["bitbank", "1day", "1", "BTC_JPY"]])
def test_add_fail_when_task_daemon_manager_raise_exception(exchange, interval, amount, pair, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.add_task", side_effect=Exception)
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-i", interval, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, interval, amount, pair", [["bitbank", "1day", "0", "BTC_JPY"]])
def test_add_with_less_than_0_amount_fail(exchange, interval, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-i", interval, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, interval, amount, pair", [["bitbank", "1day", "12.34", "BTC_JPY"]])
def test_add_with_not_int_amount_fail(exchange, interval, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-i", interval, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, interval, amount, pair", [["invalid_exchange", "1day", "10000", "BTC_JPY"]])
def test_add_with_invalid_exchange_fail(exchange, interval, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-i", interval, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, interval, amount, pair", [["bitbank", "invalid_interval", "10000", "BTC_JPY"]])
def test_add_with_invalid_interval_fail(exchange, interval, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-i", interval, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, interval, amount, pair", [["bitbank", "1day", "10000", "INVALID_PAIR"]])
def test_add_with_invalid_pair_fail(exchange, interval, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-i", interval, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("id", ["1"])
def test_remove_with_valid_id_succeed(id, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.remove_task", return_value=None)
    result = CliRunner().invoke(cli, args=["remove", id])
    assert result.exit_code == 0


@pytest.mark.parametrize("id", ["9999"])
def test_remove_with_invalid_id_fail(id, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.remove_task", side_effect=Exception)
    result = CliRunner().invoke(cli, args=["remove", id])
    assert result.exit_code != 0


@pytest.mark.parametrize("id", ["1"])
def test_start_with_valid_id_succeed(id, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.start_task", return_value=None)
    result = CliRunner().invoke(cli, args=["start", id])
    assert result.exit_code == 0


def test_start_all_tasks_succeed(mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.get_tasks", return_value=TEST_DATA)
    mocker.patch("doru.daemon_manager.DaemonManager.start_task", return_value=None)
    result = CliRunner().invoke(cli, args=["start", "--all"])
    assert result.exit_code == 0


@pytest.mark.parametrize("id", ["9999"])
def test_start_with_invalid_id_fail(id, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.start_task", side_effect=Exception)
    result = CliRunner().invoke(cli, args=["start", id])
    assert result.exit_code != 0


def test_start_with_no_id_fail():
    result = CliRunner().invoke(cli, args=["start"])
    assert result.exit_code != 0


@pytest.mark.parametrize("id", ["1"])
def test_stop_with_valid_id_succeed(id, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.stop_task", return_value=None)
    result = CliRunner().invoke(cli, args=["stop", id])
    assert result.exit_code == 0


def test_stop_all_tasks_succeed(mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.get_tasks", return_value=TEST_DATA)
    mocker.patch("doru.daemon_manager.DaemonManager.stop_task", return_value=None)
    result = CliRunner().invoke(cli, args=["stop", "--all"])
    assert result.exit_code == 0


@pytest.mark.parametrize("id", ["9999"])
def test_stop_with_invalid_id_fail(id, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.stop_task", side_effect=Exception)
    result = CliRunner().invoke(cli, args=["stop", id])
    assert result.exit_code != 0


def test_stop_with_no_id_fail():
    result = CliRunner().invoke(cli, args=["stop"])
    assert result.exit_code != 0


def test_list_with_one_or_more_tasks_succeed(mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.get_tasks", return_value=TEST_DATA)
    result = CliRunner().invoke(cli, args=["list"])
    assert result.exit_code == 0

    lines = result.stdout.split("\n")
    header = lines[0].split()
    assert (
        header[0] == "id"
        and header[1] == "pair"
        and header[2] == "amount"
        and header[3] == "interval"
        and header[4] == "exchange"
        and header[5] == "status"
    )

    words = lines[2].split()
    assert (
        words[0] == TEST_DATA[0].id
        and words[1] == TEST_DATA[0].pair
        and words[2] == str(TEST_DATA[0].amount)
        and words[3] == TEST_DATA[0].interval
        and words[4] == TEST_DATA[0].exchange
        and words[5] == TEST_DATA[0].status
    )

    words = lines[3].split()
    assert (
        words[0] == TEST_DATA[1].id
        and words[1] == TEST_DATA[1].pair
        and words[2] == str(TEST_DATA[1].amount)
        and words[3] == TEST_DATA[1].interval
        and words[4] == TEST_DATA[1].exchange
        and words[5] == TEST_DATA[1].status
    )


def test_list_with_no_task_succeed(mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.get_tasks", return_value=[])
    result = CliRunner().invoke(cli, args=["list"])
    assert result.exit_code == 0
    lines = result.stdout.split("\n")
    header = lines[0].split()
    assert (
        header[0] == "id"
        and header[1] == "pair"
        and header[2] == "amount"
        and header[3] == "interval"
        and header[4] == "exchange"
        and header[5] == "status"
    )


@pytest.mark.parametrize("exchange, key, secret", [["bitbank", "xxxxxxxxxx", "yyyyyyyyyy"]])
def test_add_credential_succeed(exchange, key, secret, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.add_cred", return_value=None)
    result = CliRunner().invoke(cli, args=["cred", "add", "--exchange", exchange, "--key", key, "--secret", secret])
    assert result.exit_code == 0


@pytest.mark.parametrize("exchange, key, secret", [["bitbank", "xxxxxxxxxx", "yyyyyyyyyy"]])
def test_add_credential_fail_when_add_cred_function_raise_exception(exchange, key, secret, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.add_cred", side_effect=Exception)
    result = CliRunner().invoke(cli, args=["cred", "add", "--exchange", exchange, "--key", key, "--secret", secret])
    assert result.exit_code != 0


@pytest.mark.parametrize(
    "exchange, key, secret",
    [["invalid_exchange", "xxxxxxxxxx", "yyyyyyyyyy"], ["bitbank", "", "yyyyyyyyyy"], ["bitbank", "xxxxxxxxxx", ""]],
)
def test_add_credential_with_invalid_params_fail(exchange, key, secret):
    result = CliRunner().invoke(cli, args=["cred", "add", "--exchange", exchange, "--key", key, "--secret", secret])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange", ["bitbank"])
def test_remove_credential_succeed(exchange, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.remove_cred", return_value=None)
    result = CliRunner().invoke(cli, args=["cred", "remove", "--exchange", exchange])
    assert result.exit_code == 0


@pytest.mark.parametrize("exchange", ["bitbank"])
def test_remove_credential_fail_when_remove_cred_function_raise_exception(exchange, mocker):
    mocker.patch("doru.daemon_manager.DaemonManager.remove_cred", side_effect=Exception)
    result = CliRunner().invoke(cli, args=["cred", "remove", "--exchange", exchange])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange", ["invalid_exchange"])
def test_remove_credential_with_invalid_param_fail(exchange):
    result = CliRunner().invoke(cli, args=["cred", "remove", "--exchange", exchange])
    assert result.exit_code != 0


def test_top_level_help():
    result = CliRunner().invoke(cli, args=["--help"])
    assert "add     Add a task to accumulate crypto." in result.stdout
    assert "remove  Remove a task to accumulate crypto." in result.stdout
    assert "start   Start tasks to accumulate crypto." in result.stdout
    assert "stop    Stop tasks to accumulate crypto." in result.stdout
    assert "list    Display tasks to accumulate crypto." in result.stdout
    assert "cred    Add or remove credentials for the exchanges." in result.stdout
