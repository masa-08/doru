import json
from datetime import datetime
from typing import List

import click
from requests import HTTPError
from tabulate import tabulate
from typing_extensions import get_args

from doru.api.client import create_client
from doru.api.schema import is_valid_exchange_name, is_valid_symbol
from doru.types import Cycle, Weekday

ENABLE_CYCLES = get_args(Cycle)
WEEKDAY = get_args(Weekday)
HEADER = ["ID", "Symbol", "Amount", "Cycle", "Next Invest Date", "Exchange", "Status"]


def validate_exchange(ctx, param, value):
    try:
        is_valid_exchange_name(value)
    except Exception as e:
        raise click.ClickException(str(e))
    return value


def validate_exchange_symbol(ctx: click.Context, param: click.Option, value):
    try:
        if param.name == "exchange":
            is_valid_exchange_name(value)
            # If symbol is specified before exchange,
            # validate symbol here because symbol is not checked.
            if "symbol" in ctx.params.keys():
                is_valid_symbol(value, ctx.params["symbol"])
        elif param.name == "symbol":
            # If symbol is specified before exchange,
            # symbol will be validated during the exchange validation
            if "exchange" not in ctx.params.keys():
                return value
            is_valid_symbol(ctx.params["exchange"], value)
        else:
            raise ValueError("Invalid param name.")
    except Exception as e:
        raise click.ClickException(str(e))
    return value


# TODO: wrap with ClickException
def validate_cred(ctx, param, value):
    if len(value) == 0:
        raise Exception("Length of API key and secret should be more than 0.")
    return value


def filter_options_about_date(ctx: click.Context, param, value: Cycle):
    def _disable_prompts(ctx: click.Context, disable_options: List[str]):
        for p in ctx.command.params:
            if isinstance(p, click.Option) and p.name in disable_options:
                p.prompt = None

    if value == "Daily":
        _disable_prompts(ctx, ["weekday", "day"])
    elif value == "Weekly":
        _disable_prompts(ctx, ["day"])
    elif value == "Monthly":
        _disable_prompts(ctx, ["weekday"])
    return value


def raise_with_response_message(e: HTTPError) -> None:
    res = json.loads(e.response.content)
    raise click.ClickException(res.get("detail"))


@click.group()
def cli():
    pass


@cli.command(help="Add a task to accumulate crypto.")
@click.option(
    "--exchange",
    "-e",
    required=True,
    type=str,
    prompt=True,
    callback=validate_exchange_symbol,
    help="Enter the exchange you will use.",
)
@click.option(
    "--symbol",
    "-s",
    required=True,
    type=str,
    prompt=True,
    callback=validate_exchange_symbol,
    help="Enter the symbol you want to buy.",
)
@click.option(
    "--cycle",
    "-c",
    required=True,
    type=click.Choice(ENABLE_CYCLES, case_sensitive=False),
    prompt=True,
    help="Select the interval at which you will purchase crypto.",
    callback=filter_options_about_date,
)
@click.option(
    "--weekday",
    "-w",
    type=click.Choice(WEEKDAY, case_sensitive=False),
    prompt=True,
    default="Sun",
    show_default=True,
    help=(
        "Select the day of the week you will purchase crypto. \
This option is enabled when the interval is set to `week`."
    ),
)
@click.option(
    "--day",
    "-d",
    type=click.IntRange(min=1, max=28),
    prompt=True,
    default=1,
    show_default=True,
    help=(
        "Enter the day in each month on which you will purchase crypto. \
This option is enabled when the interval is set to `month`."
    ),
)
@click.option(
    "--time",
    "-t",
    required=True,
    type=click.DateTime(["%H:%M"]),
    prompt=True,
    default="00:00",
    show_default=True,
    help="Enter the time you will purchase crypto.",
)
@click.option(
    "--amount",
    "-a",
    required=True,
    type=click.FloatRange(min=0, min_open=True),
    prompt=True,
    help="Enter the amount per request.",
)
@click.option(
    "--start",
    type=click.BOOL,
    prompt=True,
    default=True,
    help="Start the task after adding it.",
)
def add(
    exchange: str,
    cycle: Cycle,
    weekday: Weekday,
    day: int,
    time: datetime,
    amount: float,
    symbol: str,
    start: bool,
):
    manager = create_client()
    try:
        task = manager.add_task(
            exchange=exchange,
            cycle=cycle,
            time=datetime.strftime(time, "%H:%M"),
            amount=amount,
            symbol=symbol,
            weekday=weekday,
            day=day,
        )
        if start:
            click.echo("Successfully added.")
            manager.start_task(task.id)
    except HTTPError as e:
        raise_with_response_message(e)
    except Exception as e:
        raise click.ClickException(str(e))


@cli.command(help="Remove a task to accumulate crypto.")
@click.argument("id", nargs=1, type=click.STRING)
def remove(id: str):
    manager = create_client()
    try:
        manager.remove_task(id)
    except HTTPError as e:
        raise_with_response_message(e)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo("Successfully removed.")


@cli.command(help="Start tasks to accumulate crypto.")
@click.argument("ids", nargs=-1)
@click.option(
    "--all",
    "-a",
    required=False,
    is_flag=False,
    flag_value="all",
    help="Insert this option if you want to start all tasks.",
)
def start(ids: List[str], all: str):
    if not ids and not all:
        raise click.ClickException("Task id or `--all` option must be specified.")

    manager = create_client()
    if all:
        try:
            manager.start_all_tasks()
            click.echo("Successfully started.")
            return
        except HTTPError as e:
            raise_with_response_message(e)
        except Exception as e:
            raise click.ClickException(str(e))
    for id in ids:
        try:
            manager.start_task(id)
        except HTTPError as e:
            raise_with_response_message(e)
        except Exception as e:
            raise click.ClickException(str(e))
    click.echo("Successfully started.")


@cli.command(help="Stop tasks to accumulate crypto.")
@click.argument("ids", nargs=-1)
@click.option(
    "--all",
    "-a",
    required=False,
    is_flag=False,
    flag_value="all",
    help="Insert this option if you want to stop all tasks.",
)
def stop(ids: List[str], all: str):
    if not ids and not all:
        raise click.ClickException("Task id or `--all` option must be specified.")

    manager = create_client()
    if all:
        try:
            manager.stop_all_tasks()
            click.echo("Successfully stopped.")
            return
        except HTTPError as e:
            raise_with_response_message(e)
        except Exception as e:
            raise click.ClickException(str(e))
    for id in ids:
        try:
            manager.stop_task(id)
        except HTTPError as e:
            raise_with_response_message(e)
        except Exception as e:
            raise click.ClickException(str(e))
    click.echo("Successfully stopped.")


@cli.command(help="Display tasks to accumulate crypto.")
def list():
    manager = create_client()
    try:
        tasks = manager.get_tasks()
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo(
        tabulate(
            [(t.id, t.symbol, t.amount, t.cycle, t.next_run or "Not Scheduled", t.exchange, t.status) for t in tasks],
            headers=HEADER,
            tablefmt="simple",
        )
    )


@cli.group(help="Add or remove credentials for the exchanges.")
def cred():
    pass


@cred.command(name="add", help="Add the credential of the exchange.")
@click.option(
    "--exchange",
    "-e",
    required=True,
    type=str,
    prompt=True,
    callback=validate_exchange,
    help="Select the exchange you will use.",
)
@click.option(
    "--key",
    "-k",
    required=True,
    type=click.STRING,
    prompt=True,
    hide_input=True,
    callback=validate_cred,
    help="Enter the API key.",
)
@click.option(
    "--secret",
    "-s",
    required=True,
    type=click.STRING,
    prompt=True,
    hide_input=True,
    callback=validate_cred,
    help="Enter the API secret.",
)
def cred_add(exchange, key, secret):
    manager = create_client()
    key, secret = key.strip(), secret.strip()
    try:
        manager.add_cred(exchange, key, secret)
    except HTTPError as e:
        raise_with_response_message(e)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo("Successfully added.")


@cred.command(name="remove", help="Remove the credential of the exchange.")
@click.option(
    "--exchange",
    "-e",
    required=True,
    type=str,
    prompt=True,
    callback=validate_exchange,
    help="Select the exchange from which you want to remove the credential.",
)
def cred_remove(exchange):
    manager = create_client()
    try:
        manager.remove_cred(exchange)
    except HTTPError as e:
        raise_with_response_message(e)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo("Successfully removed.")


@cli.group(help="Terminate the background process for this application.")
def daemon():
    pass


@daemon.command(name="terminate", help="Terminate the background process for this application.")
def daemon_terminate():
    client = create_client()
    try:
        client.terminate()
    except HTTPError as e:
        raise_with_response_message(e)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo("The background process has been successfully terminated.")
