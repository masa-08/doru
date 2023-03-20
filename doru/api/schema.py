from datetime import datetime
from typing import Optional

import ccxt
from pydantic import BaseModel, root_validator, validator

from doru.type import Cycle, Status, Weekday

TIMESTAMP_STRING_FORMAT = "%Y-%m-%d %H:%M"


def is_valid_exchange_name(exchange: str):
    if exchange not in ccxt.exchanges:
        raise ValueError(f"`{exchange}` is an unsupported exchange.\n\nSupported exchanges:\n{ccxt.exchanges}")


def is_valid_symbol(exchange: str, symbol: str):
    from doru.exchange import get_exchange

    is_valid_exchange_name(exchange)
    ex = get_exchange(exchange)
    symbols = ex.fetch_spot_symbols()
    if symbol not in symbols:
        raise ValueError(f"`{symbol}` is not supported on {exchange}.\n\nSupported symbols:\n{set(symbols)}")


class TaskBase(BaseModel):
    symbol: str
    amount: float
    cycle: Cycle
    weekday: Optional[Weekday] = None
    day: Optional[int] = None
    time: str
    exchange: str

    @validator("amount")
    def amount_should_be_positive_number(cls, v, values):
        if v <= 0:
            raise ValueError("Amount should be positive value.")
        return v

    @validator("weekday", always=True)
    def weekday_validator(cls, v: Optional[Weekday], values):
        if "cycle" in values and values["cycle"] == "Weekly":
            if v is None:
                raise ValueError("The weekday parameter is required in the weekly task.")
        return v

    @validator("day", always=True)
    def day_validator(cls, v: Optional[int], values):
        if "cycle" in values and values["cycle"] == "Monthly":
            if v is None:
                raise ValueError("The day parameter is required in the monthly task.")
            if v < 1 or v > 28:
                raise ValueError("The day parameter should be between 1 and 28.")
        return v

    @validator("time")
    def time_validator(cls, v: str):
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("The time parameter should be in the following format `%H:%M`.")
        return v

    @root_validator
    def exchange_symbol_validator(cls, values):
        if "exchange" not in values:
            raise ValueError("`exchange` is required")
        if "symbol" not in values:
            raise ValueError("`symbol` is required")
        is_valid_exchange_name(values["exchange"])
        is_valid_symbol(values["exchange"], values["symbol"])
        return values


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: str
    status: Status
    next_run: Optional[str]

    @validator("id")
    def empty_id_forbidden(cls, v):
        if len(v) == 0:
            raise ValueError("Empty id is forbidden.")
        return v

    @validator("next_run")
    def next_run_should_be_specified_format(cls, v: Optional[str]):
        if v is not None:
            try:
                datetime.strptime(v, TIMESTAMP_STRING_FORMAT)
            except ValueError:
                raise ValueError("The next_run parameter should be in the following format `%Y-%m-%d %H:%M`.")
        return v


class CredentialBase(BaseModel):
    key: str
    secret: str

    @validator("key")
    def empty_key_forbidden(cls, v):
        if len(v) == 0:
            raise ValueError("Empty key is forbidden.")
        return v

    @validator("secret")
    def empty_secret_forbidden(cls, v):
        if len(v) == 0:
            raise ValueError("Empty secret is forbidden.")
        return v


class Credential(CredentialBase):
    exchange: str

    @validator("exchange")
    def exchange_validator(cls, v: str):
        is_valid_exchange_name(v)
        return v


class KeepAlive(BaseModel):
    pid: int
