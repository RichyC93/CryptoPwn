
import json, math, numpy, re, sys, time, urllib3; urllib3.disable_warnings()
from datetime import datetime
import matplotlib as mpl; mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib import interactive; interactive(False)
from mpl_finance import candlestick_ochl

plt.ioff()

url = "https://min-api.cryptocompare.com/data/"
print; Symbol = raw_input("Enter Crypto Symbol [Default: ETN]: ").upper(); print
if not Symbol: Symbol = "ETN"
print "\n\t\t-------- Select Interval --------\n"
print "  1. Use HistoMinute (Default)"
print "  2. Use HistoHour"
print "  3. Use HistoDay\n"
option = raw_input("Enter Option: ")
hist = "histohour" if option == "2" else "histoday" if option == "3" else "histominute"
url += "%s?fsym=%s&tsym=USD&limit=3000" % (hist, Symbol)
print "\n\t\t-------- Historical Data --------\n"
print "  1. Use Total History (Past 3000 %s)" % (hist[5:] + "s")
print "  2. Set Time Origin\n"
if raw_input("Enter Option: ") == "2":
    print
    month = raw_input("Enter Month [1-12]: "); month = 0 if not month.isdigit() else int(month)
    day = raw_input("Enter Day [1-31]: "); day = 0 if not day.isdigit() else int(day)
    year = raw_input("Enter Year (Default = 2018): "); year = 2018 if not year.isdigit() else int(year)
    hour = raw_input("Enter Hour [0-24]: "); hour = 0 if not hour.isdigit() else int(hour)
    minute = raw_input("Enter Minute [0-59]: "); minute = 0 if not minute.isdigit() else int(minute)
    second = raw_input("Enter Second [0-59]: "); second = 0 if not second.isdigit() else int(second)
    time_origin = time.mktime(time.struct_time([year, month, day, hour, minute, second, 0, 0, -1])) if month and day and year else 0
    if time_origin >= time.time(): time_origin = 0
    if not time_origin: print "\nInvalid Date... Using Total History"
else: time_origin = 0; print "\nUsing Total History"
print
projection_int = raw_input("Enter Projection Scale (Default: 0.6180339): ")
print "\n\t-------- Initial Price (Principal) --------\n"
print "  1. Relative To Time Origin (Default)"
print "  2. Relative To Last Price"
print "  3. Set Initial Price\n"
option = raw_input("Enter Option: ")
inital_P = 0
if option == "2": inital_P = -1
if option == "3": inital_P = float(raw_input("Enter Inital Amount: "))
source = urllib3.PoolManager().request("GET", url).data
jsonData = json.loads(source)["Data"]
candle_data = []
open_close = [[], [], [], [], []]; high_low = [[], [], [], [], []]; timestamp_date = [[[], []], [[], []], [[], []]]
last_price = (jsonData[-1]["high"] + jsonData[-1]["low"]) / 2
ochl_zero = [last_price, last_price] if inital_P < 0 else []
ochl_zero = [inital_P, inital_P] if inital_P > 0 else ochl_zero
t_zero = 0
for data in jsonData:
    condition = data["open"] and data["close"] and data["high"] and data["low"] and data["time"]
    if time_origin: condition = condition and data["time"] >= time_origin
    if condition:
        avg_open_close, avg_high_low = (data["open"] + data["close"]) / 2, (data["high"] + data["low"]) / 2
        if not ochl_zero: ochl_zero = [avg_open_close, avg_high_low] # Initital Average Prices
        open_close[0].append(data["open"]); open_close[1].append(data["close"]); open_close[2].append(avg_open_close)
        open_close[3].append((avg_open_close - ochl_zero[0]) / ochl_zero[0])
        open_close[4].append(math.log(avg_open_close) - math.log(ochl_zero[0]))
        high_low[0].append(data["high"]); high_low[1].append(data["low"]); high_low[2].append(avg_high_low)
        high_low[3].append((avg_high_low - ochl_zero[1]) / ochl_zero[1])
        high_low[4].append(math.log(avg_high_low) - math.log(ochl_zero[1]))
        if not t_zero: t_zero = data["time"] # Initital Timestamp
        local_time = time.localtime(data["time"])
        timestamp_date[0][0].append(data["time"] - t_zero); timestamp_date[1][0].append(data["time"])
        timestamp_date[2][0].append(datetime(
            int(time.strftime("%Y", local_time)), int(time.strftime("%m", local_time)),
            int(time.strftime("%d", local_time)), int(time.strftime("%H", local_time)),
            int(time.strftime("%M", local_time))
        ))
        candle_data.append([
            mpl.dates.strpdate2num("%Y %m %d %H")(time.strftime(
                "%Y %m %d %H", time.struct_time(time.localtime(data["time"])))
            ), data["open"], data["close"], data["high"], data["low"]
        ])
if not projection_int: projection_int = 0.6180339
new_ticks = int(float(projection_int) * len(timestamp_date[0][0]))
timestamp_date[0][1], timestamp_date[1][1], timestamp_date[2][1] = list(timestamp_date[0][0]), list(timestamp_date[1][0]), list(timestamp_date[2][0])
for i in range(new_ticks):
    future_seconds = 86400 if hist == "histoday" else 3600 if hist == "histohour" else 60 if hist == "histominute" else 10800
    timestamp_date[0][1].append(timestamp_date[0][1][-1] + future_seconds)
    timestamp_date[1][1].append(timestamp_date[1][1][-1] + future_seconds)
    local_time = time.localtime(timestamp_date[1][1][-1] + future_seconds)
    timestamp_date[2][1].append(datetime(
        int(time.strftime("%Y", local_time)), int(time.strftime("%m", local_time)),
        int(time.strftime("%d", local_time)), int(time.strftime("%H", local_time)),
        int(time.strftime("%M", local_time)), int(time.strftime("%S", local_time))
    ))
y_initial = [[ochl_zero[0] for i in range(len(timestamp_date[2][1]))], [0 for i in range(len(timestamp_date[2][1]))]]
print; print "%s Projection Date: %s" % (hist.title(), time.ctime(timestamp_date[1][1][-1])); print
fig1, ax = plt.subplots(2, 1)
ax[0].set_title("Average %s Price (USD)" % Symbol)
ax[0].set_ylabel("%s/USD Exchange Rate ($)" % Symbol)
ax[0].plot(timestamp_date[2][0], high_low[0], "g")
ax[0].plot(timestamp_date[2][0], high_low[1], "r")
ax[0].plot(timestamp_date[2][0], open_close[2], "b")
ax[0].plot(timestamp_date[2][1], y_initial[0], "--")
z = numpy.polyfit(timestamp_date[0][0], high_low[2], 1)
print "Average %s Price (USD) Trendline" % Symbol; print "y = %sx + (%s)" %(z[0], z[1]); print
trend_line = numpy.poly1d(z)
ax[0].plot(timestamp_date[2][1], trend_line(timestamp_date[0][1]), "--")
myFmt = DateFormatter("%b %d %y %H %M")
ax[0].xaxis.set_major_formatter(myFmt)
ax[0].get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
ax[0].get_yaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
ax[0].grid(b = True, linewidth = 1.0, which = "major")
ax[0].grid(b = True, linewidth = 0.5, which = "minor")
ax[0].minorticks_on()
ax[1].set_title("Absolute Interest Rate / Compounded Interest Rate")
ax[1].set_ylabel("Interest Rate (%)")
ax[1].plot(timestamp_date[2][0], high_low[3], "g")
z = numpy.polyfit(timestamp_date[0][0], high_low[3], 1)
print "Average Absolute Interest Trendline"; print "y = %sx + (%s)" %(z[0], z[1]); print
trend_line = numpy.poly1d(z)
ax[1].plot(timestamp_date[2][1], trend_line(timestamp_date[0][1]), "g--")
ax[1].plot(timestamp_date[2][0], high_low[4], "r")
z = numpy.polyfit(timestamp_date[0][0], high_low[4], 1)
print "Average Compound Interest Rate Trendline"; print "y = %sx + (%s)" %(z[0], z[1]); print
trend_line = numpy.poly1d(z)
ax[1].plot(timestamp_date[2][1], trend_line(timestamp_date[0][1]), "r--")
ax[1].plot(timestamp_date[2][1], y_initial[1], "--")
myFmt = DateFormatter("%b %d %y %H %M")
ax[1].xaxis.set_major_formatter(myFmt)
ax[1].get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
ax[1].get_yaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
ax[1].grid(b = True, linewidth = 1.0, which = "major")
ax[1].grid(b = True, linewidth = 0.5, which = "minor")
ax[1].minorticks_on()
fig1.autofmt_xdate()
fig2, ax2 = plt.subplots()
ax2.set_title("Candlesticks - %s/USD" % Symbol)
ax2.set_ylabel("%s/USD Exchange Rate ($)" % Symbol)
z = numpy.polyfit(timestamp_date[0][0], high_low[2], 1)
print "Average %s Price (USD) Trendline" % Symbol; print "y = %sx + (%s)" %(z[0], z[1]); print
trend_line = numpy.poly1d(z)
ax2.plot(timestamp_date[2][0], trend_line(timestamp_date[0][0]), "--")
candlestick_ochl(ax2, candle_data, width = 0.05, colorup = "#00FF00", colordown = "#CC0000")
for label in ax2.xaxis.get_ticklabels():
    label.set_rotation(45)
fig2.autofmt_xdate();
myFmt = DateFormatter("%b %d %y %H")
ax2.xaxis.set_major_formatter(myFmt)
ax2.xaxis.set_major_locator(mpl.ticker.MaxNLocator(10))
ax2.get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
ax2.get_yaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
ax2.minorticks_on()
ax2.grid(b = True, linewidth = 1.0, which = "major")
ax2.grid(b = True, linewidth = 0.5, which = "minor")
ax2.grid(True)

fig1.savefig("fig1.png"); fig2.savefig("fig2.png")
