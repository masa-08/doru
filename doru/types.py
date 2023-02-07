from typing_extensions import Literal

Exchange = Literal["bitbank", "bitflyer"]
Cycle = Literal["Daily", "Weekly", "Monthly"]
Pair = Literal["BTC_JPY", "ETH_JPY"]  # TODO: 取引所ごとに異なるペアを提示する
Status = Literal["Running", "Stopped"]
Weekday = Literal["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
