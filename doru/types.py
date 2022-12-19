from typing_extensions import Literal

Exchange = Literal["bitbank", "bitflyer"]
Interval = Literal["1day", "1week", "1month"]
Pair = Literal["BTC_JPY", "ETH_JPY"]  # TODO: 取引所ごとに異なるペアを提示する
Status = Literal["Running", "Stopped"]
