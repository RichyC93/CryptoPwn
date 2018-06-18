import plotly.offline
import plotly.plotly as py
import plotly.graph_objs as go
from datetime import datetime
import json, time, urllib3; urllib3.disable_warnings()

plotly.tools.set_credentials_file(username = "RichyC93", api_key = "T6xcBAhl2gQxuaQPXOKm")

print; Symbol = raw_input("Enter Crypto Symbol (Default: ETN): ").upper(); print
if not Symbol: Symbol = "ETN"
# "histoday": {"url": url + "histoday?fsym=ETN&tsym=USD&limit=120"},
url = "https://min-api.cryptocompare.com/data/"
MarkHist = {"url": url + "histohour?fsym=%s&tsym=USD&limit=3000" % Symbol}

source = urllib3.PoolManager().request("GET", MarkHist["url"]).data
jsonData = json.loads(source)["Data"]
open_close = [[], []]; high_low = [[], []]; dates = []
for data in jsonData:
    condition = data["time"] and data["open"] and data["close"] and data["high"] and data["low"]
    if condition:
        open_close[0].append(data["open"]); open_close[1].append(data["close"])
        high_low[0].append(data["high"]); high_low[1].append(data["low"])
        local_time = time.localtime(data["time"])
        dates.append(datetime(
            int(time.strftime("%Y", local_time)), int(time.strftime("%m", local_time)),
            int(time.strftime("%d", local_time)), int(time.strftime("%H", local_time)),
            int(time.strftime("%M", local_time), int(time.strftime("%S", local_time)))
        ))

data = [go.Candlestick(x = dates, open = open_close[0], high = high_low[0], low = high_low[1], close = open_close[1])]
plotly.offline.plot(data, filename = "test")
