
import pandas as pd
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches

from mplfinance.original_flavor import candlestick_ohlc
# No keys required for crypto data
client = CryptoHistoricalDataClient()


# Creating request object
tf = TimeFrame(amount=1, unit=TimeFrameUnit.Hour)

request_params = CryptoBarsRequest(
  symbol_or_symbols=["BTC/USD"],
  timeframe=tf,
  start=datetime(2025, 5, 1),
  end=datetime(2025, 5, 27)
)


# Retrieve daily bars for Bitcoin in a DataFrame and printing it
btc_bars = client.get_crypto_bars(request_params)
btc_df = btc_bars.df



#data.set_index('timestamp', inplace=True)

# Farbe der Candle
btc_df['color'] = btc_df.apply(lambda row: 'green' if row['close'] > row['open'] else 'red', axis=1)



# Ergebnisliste für bestätigte Strong Highs / Lows
structure = []

# Temporäre und letzte Zeichen
candidate_WH = None
candidate_WL = None
last_SH = None
last_SL = None
last_State = None
# Zähler für gleichfarbige Kerzen
up_count = 0
down_count = 0

# Temporäre Extrema
max_high = None
max_high_time = None
min_low = None
min_low_time = None

for i in range(1, len(btc_df)):
    prev = btc_df.iloc[i-1]
    curr = btc_df.iloc[i]

    # ————— Trendzählung & Extrema aktualisieren —————
    if curr['color'] == 'green':
        if max_high is None or curr['high'] > max_high:
            max_high = curr['high']
            max_high_time = curr.name
        # Aufwärts-Count
        if prev['color'] == 'green':
            up_count += 1
        else:
            up_count = 1
        down_count = 0
        # Tief-Temp zurücksetzen
        #min_low = None
        #min_low_time = None

    elif curr['color'] == 'red':
        if min_low is None or curr['low'] < min_low:
            min_low = curr['low']
            min_low_time = curr.name
        # Abwärts-Count
        if prev['color'] == 'red':
            down_count += 1
        else:
            down_count = 1
        up_count = 0



        # Hoch-Temp zurücksetzen
        #max_high = None
        #max_high_time = None

    else:
        # Falls andere Farbe / NaN
        up_count = down_count = 0
        max_high = max_high_time = None
        min_low = min_low_time = None


        #max_high = max_high_time = None


        #min_low = min_low_time = None

    # ————— 1) Weak High erkennen (nach 2 roten Kerzen) —————
    if down_count == 2 and candidate_WH is None and max_high_time is not None:
        candidate_WH = {'time': max_high_time, 'price': max_high}

    # ————— 2) Weak Low erkennen (nach 2 grünen Kerzen) —————
    if up_count == 2 and candidate_WL is None and min_low_time is not None:
        candidate_WL = {'time': min_low_time, 'price': min_low}

    # ————— 3) Conversion WH → SH (bei 2 grünen Kerzen nach WH) —————
    if candidate_WH is not None and up_count == 2:
        if min_low_time is not None:
            # a) neues Weak Low zwischenspeichern
            candidate_WL = {'time': min_low_time, 'price': min_low}

        # b) nur zum Strong High machen, wenn höher als letztes SH
        if last_SH is None or candidate_WH['price'] > last_SH['price'] and last_State != 'High': # and last state not HIGH or LOW
            structure.append({
                'type':  'Strong High',
                'time':  candidate_WH['time'],
                'price': candidate_WH['price']
            })
            last_SH = candidate_WH
            last_State = 'High'

        # c) WH zurücksetzen
        candidate_WH = None         
        max_high = max_high_time = None


    # ————— 4) Conversion WL → SL (bei 2 roten Kerzen nach WL) —————
    if candidate_WL is not None and down_count == 2:
        if max_high_time is not None:
            # a) neues Weak High zwischenspeichern
            candidate_WH = {'time': max_high_time, 'price': max_high}

        # b) nur zum Strong Low machen, wenn tiefer als letztes SL
        if last_SL is None or candidate_WL['price'] < last_SL['price'] and last_State != 'Low':
            structure.append({
                'type':  'Strong Low',
                'time':  candidate_WL['time'],
                'price': candidate_WL['price']
            })
            last_SL = candidate_WL
            last_State = 'Low' 
        # c) WL zurücksetzen
        candidate_WL = None
        min_low = min_low_time = None



##########################################


structure_df = pd.DataFrame(structure)
print(structure_df)


btc_df = btc_df.reset_index(level=0, drop=True)
# stelle sicher, dass der Index als DatetimeIndex vorliegt
btc_df.index = pd.to_datetime(btc_df.index)

ohlc = btc_df.copy()
ohlc['t_num'] = mdates.date2num(ohlc.index.to_pydatetime())
ohlc_vals = ohlc[['t_num','open','high','low','close']].values

fig, ax = plt.subplots(figsize=(12,6))


candlestick_ohlc(
    ax,
    ohlc_vals,
    width=0.03,           # Breite der Kerzen
    colorup='green',      # Aufwärtskerze
    colordown='red'       # Abwärtskerze
)



structure_df['time'] = structure_df['time'].apply(lambda x: x[1] if isinstance(x, tuple) else x)
structure_df['time'] = pd.to_datetime(structure_df['time'])


sh = structure_df[structure_df['type']=='Strong High']
structure_df['time'] = pd.to_datetime(structure_df['time'])
times_sh = sh['time'].dt.to_pydatetime()


ax.scatter(
    mdates.date2num(times_sh),
    sh['price'],
    marker='^',
    s=100,
    color='green',
    label='Strong High'
)


# Strong Lows: rote Dreiecke nach unten
sl = structure_df[structure_df['type']=='Strong Low']
times_sl = sl['time'].dt.to_pydatetime()


ax.scatter(
    mdates.date2num(times_sl),
    sl['price'],
    marker='v',
    s=100,
    color='red',
    label='Strong Low'
)
times_seq = structure_df['time'].dt.to_pydatetime()
prices_seq = structure_df['price'].values
#   – in Matplotlib-Zahlen
nums_seq = mdates.date2num(times_seq)

ax.plot(
    nums_seq,
    prices_seq,
    linestyle='-',
    linewidth=1,
    color='blue',
    label='Struktur-Verlauf'
)

# 5) Achsen formatieren
ax.xaxis_date()
ax.xaxis.set_major_locator(mdates.HourLocator(interval=10))

ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d-%H:%M'))
plt.xticks(rotation=45)
ax.set_xlabel('Zeit')
ax.set_ylabel('Preis USD')
plt.title('BTC/USD – Stundenkerzen mit Strong Highs/Lows')
plt.legend()
plt.tight_layout()
plt.show()

