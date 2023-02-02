import json
from typing import List

import click
from requests import HTTPError
from tabulate import tabulate
from typing_extensions import get_args

from doru.api.client import create_client
from doru.types import Exchange, Interval, Pair

ENABLE_EXCHANGES = get_args(Exchange)
ENABLE_INTERVALS = get_args(Interval)
ENABLE_PAIRS = get_args(Pair)
HEADER = ["id", "pair", "amount", "interval", "exchange", "status"]


def validate_cred(ctx, param, value):
    if len(value) == 0:
        raise Exception("Length of API key and secret should be more than 0.")
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
    type=click.Choice(ENABLE_EXCHANGES, case_sensitive=False),
    prompt=True,
    help="Select the exchange you will use.",
)
@click.option(
    "--interval",
    "-i",
    required=True,
    type=click.Choice(ENABLE_INTERVALS, case_sensitive=False),
    prompt=True,
    help="Select the interval at which you will purchase crypto.",
)
@click.option(
    "--amount",
    "-a",
    required=True,
    type=click.IntRange(min=1),
    prompt=True,
    help="Enter the amount per request. (unit: yen)",
)
@click.option(
    "--pair",
    "-p",
    required=True,
    type=click.Choice(ENABLE_PAIRS, case_sensitive=False),
    prompt=True,
    help="Select the pair you want to buy.",
)
@click.option(
    "--start",
    "-s",
    type=click.BOOL,
    prompt=True,
    default=True,
    help="Start the task after adding it.",
)
def add(exchange: Exchange, interval: Interval, amount: int, pair: Pair, start: bool):
    manager = create_client()
    try:
        task = manager.add_task(exchange, interval, amount, pair)
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
            [(t.id, t.pair, t.amount, t.interval, t.exchange, t.status) for t in tasks],
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
    type=click.Choice(ENABLE_EXCHANGES, case_sensitive=False),
    prompt=True,
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
    type=click.Choice(ENABLE_EXCHANGES, case_sensitive=False),
    prompt=True,
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
