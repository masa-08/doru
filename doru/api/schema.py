from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator

from doru.types import Cycle, Exchange, Pair, Status, Weekday


class TaskBase(BaseModel):
    pair: Pair
    amount: int
    cycle: Cycle
    weekday: Optional[Weekday] = None
    day: Optional[int] = None
    time: str
    exchange: Exchange

    @validator("amount")
    def amount_should_be_positive_number(cls, v):
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


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: str
    status: Status

    @validator("id")
    def empty_id_forbidden(cls, v):
        if len(v) == 0:
            raise ValueError("Empty id is forbidden.")
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
    exchange: Exchange


class KeepAlive(BaseModel):
    pid: int
