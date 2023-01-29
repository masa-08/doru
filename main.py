import asyncio

import click
from requests.exceptions import RequestException

from doru.api.daemonize import run
from doru.cli import cli
from doru.logger import init_logger

if __name__ == "__main__":
    init_logger()
    try:
        cli()
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
        try:
            cli()
        except RequestException:
            print("There is some kind of communication problem with a background process")
            exit(1)
