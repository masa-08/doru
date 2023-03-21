import os
from logging import config
from pathlib import Path

from doru.envs import DORU_LOG_FILE

LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"default": {"format": "%(asctime)s %(levelname)s: %(name)s[%(funcName)s:%(lineno)s]: %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "level": "INFO", "formatter": "default"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "default",
            "filename": Path(DORU_LOG_FILE).expanduser(),
            "mode": "a",
            "maxBytes": 1000000,  # 100KB
            "backupCount": 3,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "doru": {"level": "INFO", "handlers": ["file"], "propagate": False},
        "uvicorn": {"level": "INFO", "handlers": ["file"], "propagate": False},
    },
}


def init_logger() -> None:
    log_dir = Path(LOGGER_CONFIG["handlers"]["file"]["filename"]).expanduser().parent  # type: ignore[index]
    if not os.path.isdir(log_dir):
        log_dir.mkdir(parents=True)
    config.dictConfig(LOGGER_CONFIG)
