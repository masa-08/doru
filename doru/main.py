from doru.cli import cli, start_up_operation
from doru.logger import init_logger


def main() -> None:
    init_logger()
    start_up_operation()
    cli()
