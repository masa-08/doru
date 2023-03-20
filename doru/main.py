from doru.cli import cli, start_up_operation
from doru.logger import init_logger

if __name__ == "__main__":
    init_logger()
    start_up_operation()
    cli()
