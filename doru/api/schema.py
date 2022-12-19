from pydantic import BaseModel

from doru.types import Exchange, Interval, Pair, Status


class TaskBase(BaseModel):
    pair: Pair
    amount: int
    interval: Interval
    exchange: Exchange


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: str
    status: Status


class Credential(BaseModel):
    exchange: Exchange
    key: str
    secret: str
