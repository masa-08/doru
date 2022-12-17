from typing_extensions import Literal, TypedDict

Exchange = Literal["bitbank", "bitflyer"]
Interval = Literal["1day", "1week", "1month"]
Pair = Literal["BTC_JPY", "ETH_JPY"]  # TODO: 取引所ごとに異なるペアを提示する
Status = Literal["Running", "Stopped"]


class Task(TypedDict):
    id: str
    pair: Pair
    amount: int
    interval: Interval
    exchange: Exchange
    status: Status


class Credential(TypedDict):
    exchange: Exchange
    key: str
    secret: str
