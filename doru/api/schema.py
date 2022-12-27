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
