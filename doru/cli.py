from typing import List

import click
from tabulate import tabulate
from typing_extensions import get_args

from doru.daemon_manager import create_daemon_manager
from doru.types import Exchange, Interval, Pair

ENABLE_EXCHANGES = get_args(Exchange)
ENABLE_INTERVALS = get_args(Interval)
ENABLE_PAIRS = get_args(Pair)


def validate_cred(ctx, param, value):
    if len(value) == 0:
        raise Exception("Length of API key and secret should be more than 0.")
    return value


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
def add(exchange: Exchange, interval: Interval, amount: int, pair: Pair):
    manager = create_daemon_manager()
    task_id = "hoge"  # XXX
    try:
        manager.add_task(
            {
                "id": task_id,
                "exchange": exchange,
                "interval": interval,
                "amount": amount,
                "pair": pair,
                "status": "Stopped",
            }
        )
        manager.start_task(task_id)  # XXX
    except Exception as e:
        raise click.ClickException(str(e))  # XXX


@cli.command(help="Remove a task to accumulate crypto.")
@click.argument("id", nargs=1, type=click.STRING)
def remove(id: str):
    manager = create_daemon_manager()
    try:
        manager.remove_task(id)
    except Exception as e:
        raise click.ClickException(str(e))  # XXX


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

    manager = create_daemon_manager()
    if all:
        try:
            manager.start_all_tasks()
            return
        except Exception as e:
            raise click.ClickException(str(e))  # XXX
    for id in ids:
        try:
            manager.start_task(id)
        except Exception as e:
            raise click.ClickException(str(e))  # XXX


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

    manager = create_daemon_manager()
    if all:
        try:
            manager.stop_all_tasks()
            return
        except Exception as e:
            raise click.ClickException(str(e))  # XXX
    for id in ids:
        try:
            manager.stop_task(id)
        except Exception as e:
            raise click.ClickException(str(e))  # XXX


@cli.command(help="Display tasks to accumulate crypto.")
def list():
    manager = create_daemon_manager()
    try:
        tasks = manager.get_tasks()
    except Exception as e:
        raise click.ClickException(str(e))  # XXX
    click.echo(tabulate(tasks, headers="keys", tablefmt="simple"))


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
    manager = create_daemon_manager()
    try:
        manager.add_cred({"exchange": exchange, "key": key, "secret": secret})
    except Exception as e:
        raise click.ClickException(str(e))  # XXX


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
    manager = create_daemon_manager()
    try:
        manager.remove_cred(exchange)
    except Exception as e:
        raise click.ClickException(str(e))  # XXX