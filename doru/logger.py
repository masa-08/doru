import json
from logging import config


def init_logger() -> None:
    with open("log_config.json", "r") as f:
        log_conf = json.load(f)
    config.dictConfig(log_conf)
