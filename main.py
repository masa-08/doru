import asyncio

import click
from requests.exceptions import RequestException

from doru.api.client import create_client
from doru.api.daemonize import run
from doru.cli import cli
from doru.logger import init_logger

if __name__ == "__main__":
    init_logger()

    client = create_client()
    try:
        client.keepalive()
    except RequestException:
        click.echo("The background process of this application is starting up...")
        try:
            asyncio.run(run())
        except asyncio.TimeoutError as e:
            click.echo("The startup of the background process terminated due to timeout...")
            exit(1)
        except Exception:
            click.echo("Something wrong with the startup of the background process...")
            exit(1)

        click.echo("The background process of this application has been successfully started!")
        click.echo("---------------------------------------------------------------------------")

    cli()
