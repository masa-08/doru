from typing import List

import pytest
from click.testing import CliRunner

from doru.api.client import Client
from doru.api.schema import Task
from doru.cli import cli

TEST_DATA: List[Task] = [
    Task(
        id="1",
        exchange="bitbank",
        cycle="Daily",
        time="00:00",
        amount=10000,
        pair="BTC/JPY",
        status="Stopped",
    ),
    Task(
        id="2",
        cycle="Weekly",
        weekday="Mon",
        time="23:59",
        exchange="bitflyer",
        amount=20000,
        pair="ETH/JPY",
        status="Running",
        next_run="2022-01-01 00:00",
    ),
    Task(
        id="3",
        cycle="Monthly",
        day=28,
        time="23:59",
        exchange="bitflyer",
        amount=0.00001,
        pair="ETH/BTC",
        status="Stopped",
    ),
]


@pytest.mark.parametrize("exchange, cycle, amount, pair", [["bitbank", "Daily", "1", "BTC/JPY"]])
def test_add_with_valid_amount_succeed(exchange, cycle, amount, pair, mocker):
    mocker.patch("doru.api.client.Client.add_task", return_value=TEST_DATA[1])
    mocker.patch("doru.api.client.Client.start_task", return_value=None)
    spy = mocker.spy(Client, "start_task")
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-c", cycle, "-a", amount, "-p", pair])
    assert result.exit_code == 0
    assert spy.call_count == 1


@pytest.mark.parametrize("exchange, cycle, amount, pair, start", [["bitbank", "Daily", "1", "BTC/JPY", "False"]])
def test_add_with_valid_amount_and_not_start_flag_succeed(exchange, cycle, amount, pair, start, mocker):
    mocker.patch("doru.api.client.Client.add_task", return_value=TEST_DATA[1])
    spy = mocker.spy(Client, "start_task")
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-c", cycle, "-a", amount, "-p", pair, "-s", start])
    assert result.exit_code == 0
    assert spy.call_count == 0


@pytest.mark.parametrize("exchange, cycle, amount, pair", [["bitbank", "Daily", "1", "BTC/JPY"]])
def test_add_fail_when_task_daemon_manager_raise_exception(exchange, cycle, amount, pair, mocker):
    mocker.patch("doru.api.client.Client.add_task", side_effect=Exception)
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-c", cycle, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, cycle, weekday, amount, pair", [["bitbank", "Weekly", "invalid", "1", "BTC/JPY"]])
def test_add_weekly_task_with_invalid_weekday_option_fail(exchange, cycle, weekday, amount, pair):
    result = CliRunner().invoke(
        cli, args=["add", "-e", exchange, "-c", cycle, "-w", weekday, "-a", amount, "-p", pair]
    )
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, cycle, day, amount, pair", [["bitbank", "Monthly", "29", "1", "BTC/JPY"]])
def test_add_monthly_task_with_invalid_day_option_fail(exchange, cycle, day, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-c", cycle, "-d", day, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, cycle, time, amount, pair", [["bitbank", "Daily", "24:00", "1", "BTC/JPY"]])
def test_add_task_with_invalid_time_option_fail(exchange, cycle, time, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-c", cycle, "-t", time, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, cycle, amount, pair", [["bitbank", "Daily", "0", "BTC/JPY"]])
def test_add_with_less_than_0_amount_fail(exchange, cycle, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-c", cycle, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, cycle, amount, pair", [["bitflyer", "Monthly", "0.00001", "ETH/BTC"]])
def test_add_with_more_than_0_amount_succeed(exchange, cycle, amount, pair, mocker):
    mocker.patch("doru.api.client.Client.add_task", return_value=TEST_DATA[2])
    mocker.patch("doru.api.client.Client.start_task", return_value=None)
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-c", cycle, "-a", amount, "-p", pair])
    assert result.exit_code == 0


@pytest.mark.parametrize("exchange, cycle, amount, pair", [["invalid_exchange", "Daily", "10000", "BTC/JPY"]])
def test_add_with_invalid_exchange_fail(exchange, cycle, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-c", cycle, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, cycle, amount, pair", [["bitbank", "invalid_cycle", "10000", "BTC/JPY"]])
def test_add_with_invalid_cycle_fail(exchange, cycle, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-c", cycle, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("exchange, cycle, amount, pair", [["bitbank", "Daily", "10000", "INVALID_PAIR"]])
def test_add_with_invalid_pair_fail(exchange, cycle, amount, pair):
    result = CliRunner().invoke(cli, args=["add", "-e", exchange, "-c", cycle, "-a", amount, "-p", pair])
    assert result.exit_code != 0


@pytest.mark.parametrize("id", ["1"])
def test_remove_with_valid_id_succeed(id, mocker):
    mocker.patch("doru.api.client.Client.remove_task", return_value=None)
    result = CliRunner().invoke(cli, args=["remove", id])
    assert result.exit_code == 0


@pytest.mark.parametrize("id", ["9999"])
def test_remove_with_invalid_id_fail(id, mocker):
    mocker.patch("doru.api.client.Client.remove_task", side_effect=Exception)
    result = CliRunner().invoke(cli, args=["remove", id])
    assert result.exit_code != 0


@pytest.mark.parametrize("id", ["1"])
def test_start_with_valid_id_succeed(id, mocker):
    mocker.patch("doru.api.client.Client.start_task", return_value=None)
    result = CliRunner().invoke(cli, args=["start", id])
    assert result.exit_code == 0


def test_start_all_tasks_succeed(mocker):
    mocker.patch("doru.api.client.Client.get_tasks", return_value=TEST_DATA)
    mocker.patch("doru.api.client.Client.start_task", return_value=None)
    result = CliRunner().invoke(cli, args=["start", "--all"])
    assert result.exit_code == 0


@pytest.mark.parametrize("id", ["9999"])
def test_start_with_invalid_id_fail(id, mocker):
    mocker.patch("doru.api.client.Client.start_task", side_effect=Exception)
    result = CliRunner().invoke(cli, args=["start", id])
    assert result.exit_code != 0


def test_start_with_no_id_fail():
    result = CliRunner().invoke(cli, args=["start"])
    assert result.exit_code != 0


@pytest.mark.parametrize("id", ["1"])
def test_stop_with_valid_id_succeed(id, mocker):
    mocker.patch("doru.api.client.Client.stop_task", return_value=None)
    result = CliRunner().invoke(cli, args=["stop", id])
    assert result.exit_code == 0


def test_stop_all_tasks_succeed(mocker):
    mocker.patch("doru.api.client.Client.get_tasks", return_value=TEST_DATA)
    mocker.patch("doru.api.client.Client.stop_task", return_value=None)
    result = CliRunner().invoke(cli, args=["stop", "--all"])
    assert result.exit_code == 0


@pytest.mark.parametrize("id", ["9999"])
def test_stop_with_invalid_id_fail(id, mocker):
    mocker.patch("doru.api.client.Client.stop_task", side_effect=Exception)
    result = CliRunner().invoke(cli, args=["stop", id])
    assert result.exit_code != 0


def test_stop_with_no_id_fail():
    result = CliRunner().invoke(cli, args=["stop"])
    assert result.exit_code != 0


def test_list_with_one_or_more_tasks_succeed(mocker):
    mocker.patch("doru.api.client.Client.get_tasks", return_value=TEST_DATA)
    result = CliRunner().invoke(cli, args=["list"])
    assert result.exit_code == 0

    lines = result.stdout.split("\n")
    header = lines[0].split()
    assert (
        header[0] == "ID"
        and header[1] == "Pair"
        and header[2] == "Amount"
        and header[3] == "Cycle"
        and " ".join(header[4:7]) == "Next Invest Date"
        and header[7] == "Exchange"
        and header[8] == "Status"
    )

    words = lines[2].split()
    assert (
        words[0] == TEST_DATA[0].id
        and words[1] == TEST_DATA[0].pair
        and words[2] == str(int(TEST_DATA[0].amount))
        and words[3] == TEST_DATA[0].cycle
        and " ".join(words[4:6]) == "Not Scheduled"
        and words[6] == TEST_DATA[0].exchange
        and words[7] == TEST_DATA[0].status
    )

    words = lines[3].split()
    assert (
        words[0] == TEST_DATA[1].id
        and words[1] == TEST_DATA[1].pair
        and words[2] == str(int(TEST_DATA[1].amount))
        and words[3] == TEST_DATA[1].cycle
        and " ".join(words[4:6]) == TEST_DATA[1].next_run
        and words[6] == TEST_DATA[1].exchange
        and words[7] == TEST_DATA[1].status
    )

    words = lines[4].split()
    assert (
        words[0] == TEST_DATA[2].id
        and words[1] == TEST_DATA[2].pair
        and words[2] == str(TEST_DATA[2].amount)
        and words[3] == TEST_DATA[2].cycle
        and " ".join(words[4:6]) == "Not Scheduled"
        and words[6] == TEST_DATA[2].exchange
        and words[7] == TEST_DATA[2].status
    )


def test_list_with_no_task_succeed(mocker):
    mocker.patch("doru.api.client.Client.get_tasks", return_value=[])
    result = CliRunner().invoke(cli, args=["list"])
    assert result.exit_code == 0
    lines = result.stdout.split("\n")
    header = lines[0].split()
    assert (
        header[0] == "ID"
        and header[1] == "Pair"
        and header[2] == "Amount"
        and header[3] == "Cycle"
        and " ".join(header[4:7]) == "Next Invest Date"
        and header[7] == "Exchange"
        and header[8] == "Status"
    )


@pytest.mark.parametrize("exchange, expected_key, expected_secret", [("bitbank", "xxxxxxxxxx", "yyyyyyyyyy")])
@pytest.mark.parametrize(
    "key, secret",
    [
        ("xxxxxxxxxx", "yyyyyyyyyy"),
        (" xxxxxxxxxx ", " yyyyyyyyyy "),
        ("\nxxxxxxxxxx\n", "\nyyyyyyyyyy\n"),
        ("\txxxxxxxxxx\t", "\tyyyyyyyyyy\t"),
    ],
)
def test_add_credential_succeed(exchange, key, secret, expected_key, expected_secret, mocker):
    mock = mocker.patch("doru.api.client.Client.add_cred", return_value=None)
    result = CliRunner().invoke(cli, args=["cred", "add", "--exchange", exchange, "--key", key, "--secret", secret])
    assert result.exit_code == 0

    mock_args = mock.call_args_list
    assert mock_args[0][0] == (exchange, expected_key, expected_secret)


@pytest.mark.parametrize("exchange, key, secret", [["bitbank", "xxxxxxxxxx", "yyyyyyyyyy"]])
def test_add_credential_fail_when_add_cred_function_raise_exception(exchange, key, secret, mocker):
    mocker.patch("doru.api.client.Client.add_cred", side_effect=Exception)
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
    mocker.patch("doru.api.client.Client.remove_cred", return_value=None)
    result = CliRunner().invoke(cli, args=["cred", "remove", "--exchange", exchange])
    assert result.exit_code == 0


@pytest.mark.parametrize("exchange", ["bitbank"])
def test_remove_credential_fail_when_remove_cred_function_raise_exception(exchange, mocker):
    mocker.patch("doru.api.client.Client.remove_cred", side_effect=Exception)
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
