from pydantic import BaseModel, validator

from doru.types import Exchange, Interval, Pair, Status


class TaskBase(BaseModel):
    pair: Pair
    amount: int
    interval: Interval
    exchange: Exchange

    @validator("amount")
    def amount_should_be_positive_number(cls, v):
        if v <= 0:
            raise ValueError("Amount should be positive value.")
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
